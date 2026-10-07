import frappe
import json
from frappe import _

@frappe.whitelist(allow_guest=False)
def get_distributor_dashboard_info():
    """
    Return distributor dashboard rows with current enrollment status, document status,
    and full enrollment history (including re-enrollments).
    """
    frappe.only_for("Supervisor")
    
    # Main dataset: latest enrollment per member and preferred document for that course
    main_sql = """
        SELECT
            d.name                                AS `distributo_docid`,
            d.attendee_name                       AS `attendee_name`,
            d.designation                         AS `designation`,
            d.user_id                             AS `distributor_user_id`,
            IFNULL(CAST(d.login_reminder_count AS CHAR), '0') AS `login_remainer_count`,
            d.distributor_email_address           AS `distributor_email_address`,
            d.distributor_contact_number          AS `distributor_contact_number`,
            d.distributor_company_name            AS `distributor_company_name`,
            d.account__distributor_code           AS `account_distributor_code`,
            d.distributor_name                    AS `distributor_name`,
            d.rsm__state_head                     AS `distributor_rsm_state_head`,
            d.bu__fd_head                         AS `distributor_bu__fd_head`,
            (
                SELECT GROUP_CONCAT(CONCAT(mddc.division, ':', mddc.meril_company_name) SEPARATOR '; ')
                FROM `tabMeril Distributor Division Child` AS mddc
                WHERE mddc.parent = d.name
            )                                     AS `divisions_meril_company_names`,
            d.distributor_company_address         AS `distributor_company_address`,
            d.country                             AS `country`,
            d.city                                AS `city`,
            d.region                              AS `region`,
            d.state                               AS `state`,
            le.course                             AS `course_name`,
            le.progress                           AS `progress`,
            le.completed_on                       AS `completed_on`,
            IFNULL(le.completion_status, 'Pending') AS `completion_status`,
            IFNULL(CAST(le.re_enrollment_count AS CHAR), '0') AS `re_enrollment_count`,
            dcd.has_submitted_documents           AS `submitted_documents`,
            dcd.submission_datetime               AS `submission_datetime`,
            dcd.name                              AS `docuemnts_id`
        FROM `tabDistributor` AS d
        LEFT JOIN (
            SELECT le1.*
            FROM `tabLMS Enrollment` AS le1
            JOIN (
                SELECT member, course, MAX(enrollment_version) AS max_ev
                FROM `tabLMS Enrollment`
                GROUP BY member, course
            ) AS latest
            ON latest.member = le1.member
               AND latest.course = le1.course
               AND latest.max_ev = le1.enrollment_version
        ) AS le
            ON le.member = d.user_id
        LEFT JOIN `tabDistributor Course Documents` AS dcd
            ON dcd.name = (
                SELECT d2.name
                FROM `tabDistributor Course Documents` AS d2
                WHERE d2.distributor = d.name
                  AND d2.course = le.course
                ORDER BY d2.is_current_enrollment DESC, d2.enrollment_version DESC, d2.modified DESC
                LIMIT 1
            )
        ORDER BY d.distributor_name
    """
    rows = frappe.db.sql(main_sql, as_dict=True)

    # Build enrollment history for all distributors in one query
    members = [r.get("distributor_user_id") for r in rows if r.get("distributor_user_id")]
    history_by_member = {}
    if members:
        history_sql = """
            SELECT
                d.user_id                           AS member,
                le.course                           AS course,
                le.enrollment_version               AS enrollment_version,
                le.progress                         AS progress,
                le.completed_on                     AS completed_on,
                IFNULL(le.completion_status, 'Pending') AS completion_status,
                dcd.name                            AS docid,
                dcd.has_submitted_documents         AS submitted,
                dcd.submission_datetime             AS submission_datetime
            FROM `tabDistributor` AS d
            JOIN `tabLMS Enrollment` AS le
                ON le.member = d.user_id
            LEFT JOIN `tabDistributor Course Documents` AS dcd
                ON dcd.distributor = d.name
               AND dcd.course = le.course
               AND dcd.enrollment_version = le.enrollment_version
            WHERE d.user_id IN %(members)s
            ORDER BY d.user_id, le.enrollment_version ASC
        """
        hist_rows = frappe.db.sql(history_sql, {"members": tuple(set(members))}, as_dict=True)
        for hr in hist_rows:
            # Derive completed status if progress is 100
            progress_val = float(hr.get("progress") or 0)
            status = hr.get("completion_status") or "Pending"
            if progress_val >= 100.0 and status != "Completed":
                status = "Completed"
            entry = {
                "course": hr.get("course"),
                "enrollment_version": hr.get("enrollment_version"),
                "progress": hr.get("progress"),
                "completed_on": hr.get("completed_on"),
                "completion_status": status,
                "documents": []
            }
            if hr.get("docid"):
                entry["documents"].append({
                    "name": hr.get("docid"),
                    "docid": hr.get("docid"),
                    "submitted": bool(hr.get("submitted")),
                    "submission_datetime": hr.get("submission_datetime"),
                })
            history_by_member.setdefault(hr["member"], []).append(entry)

    # Final post-processing
    for r in rows:
        # Normalize completion from progress
        try:
            prog = float(r.get("progress") or 0)
        except Exception:
            prog = 0.0
        if prog >= 100.0 and r.get("completion_status") != "Completed":
            r["completion_status"] = "Completed"
        # Attach history
        r["enrollment_history"] = history_by_member.get(r.get("distributor_user_id"), [])
        # Ensure booleans/datetimes are present
        r["submitted_documents"] = bool(r.get("submitted_documents"))
    return rows


@frappe.whitelist(allow_guest=False)
def get_employee_dashboard_info():
    """
    Returns all employees' info using a direct SQL query with LEFT JOIN to include
    document submission data per course, and also includes course progress, completion status,
    and course completion datetime from LMS Enrollment where course matches.

    LMS Enrollment fields: progress, completed_on, completion_status, member.
    """
    
    frappe.only_for("Supervisor")

    region_expr = "COALESCE(e.branch, '')"
    for candidate in ("region", "custom_region"):
        if frappe.db.has_column("Employee", candidate):
            region_expr = f"COALESCE(e.{candidate}, '')"
            break

    login_expr = "'0'"
    login_sources = (
        ("Employee", "login_reminder_count", "e"),
        ("Employee", "custom_login_reminder_count", "e"),
        ("LMS Enrollment", "login_reminder_count", "le"),
    )
    for table, field, alias in login_sources:
        if frappe.db.has_column(table, field):
            login_expr = f"IFNULL(CAST({alias}.{field} AS CHAR), '0')"
            break

    hod_expr = "''"
    hod_join = ""
    if frappe.db.has_column("Employee", "hod_name"):
        hod_expr = "COALESCE(e.hod_name, '')"
    elif frappe.db.has_column("Employee", "custom_hod_name"):
        hod_expr = "COALESCE(e.custom_hod_name, '')"
    elif frappe.db.has_column("Department", "hod_name"):
        hod_expr = "COALESCE(dept.hod_name, '')"
        hod_join = """
            LEFT JOIN `tabDepartment` AS dept
                ON dept.name = e.department
        """
    elif frappe.db.has_column("Department", "hod"):
        hod_expr = "COALESCE(hod_emp.employee_name, '')"
        hod_join = """
            LEFT JOIN `tabDepartment` AS dept
                ON dept.name = e.department
            LEFT JOIN `tabEmployee` AS hod_emp
                ON hod_emp.name = dept.hod
        """

    query = f"""
        SELECT
            e.name                             AS `employee_docid`,
            e.employee_name                    AS `employee_name`,
            e.custom_employee_id               AS `custom_employee_id`,
            e.company                          AS `company`,
            e.designation                      AS `designation`,
            e.department                       AS `department`,
            COALESCE(manager.employee_name, '') AS `reporting_head_name`,
            e.company_email                    AS `company_email`,
            COALESCE(e.employee_number, e.cell_number, '') AS `employee_number`,
            e.country                          AS `country`,
            {region_expr}                      AS `region`,
            {login_expr}                       AS `login_reminder_count`,
            {hod_expr}                         AS `hod_name`,
            e.user_id                          AS `employee_user_id`,
            le.course                          AS `course_name`,
            IFNULL(CAST(le.course_reminder_count AS CHAR), '0') AS `course_reminder_count`,
            IFNULL(le.progress, 0)             AS `progress`,
            le.completed_on                    AS `completed_on`,
            IFNULL(le.completion_status, 'Pending') AS `completion_status`,
            COALESCE(le.enrollment_version, 1) AS `enrollment_version`,
            (
                SELECT ed_inner.name
                FROM `tabEmployee Course Documents` AS ed_inner
                WHERE ed_inner.employee = e.name
                  AND ed_inner.course = le.course
                ORDER BY (ed_inner.enrollment_version = le.enrollment_version) DESC,
                         ed_inner.is_current_enrollment DESC,
                         ed_inner.modified DESC
                LIMIT 1
            ) AS `docuemnts_id`
        FROM `tabEmployee` AS e
        LEFT JOIN `tabEmployee` AS manager
            ON manager.name = e.reports_to
        LEFT JOIN (
            SELECT le1.*
            FROM `tabLMS Enrollment` AS le1
            JOIN (
                SELECT member, course, MAX(enrollment_version) AS max_ev
                FROM `tabLMS Enrollment`
                GROUP BY member, course
            ) AS latest
            ON latest.member = le1.member
               AND latest.course = le1.course
               AND latest.max_ev = le1.enrollment_version
        ) AS le
            ON le.member = e.user_id
        {hod_join}
        ORDER BY e.employee_name, le.course
    """

    data = frappe.db.sql(query, as_dict=True)

    # Build enrollment history for all employees in one query
    members = [r.get("employee_user_id") for r in data if r.get("employee_user_id")]
    history_by_member = {}
    if members:
        history_sql = """
            SELECT
                e.user_id                           AS member,
                le.course                           AS course,
                le.enrollment_version               AS enrollment_version,
                le.progress                         AS progress,
                le.completed_on                     AS completed_on,
                IFNULL(le.completion_status, 'Pending') AS completion_status,
                ecd.name                            AS docid,
                ecd.has_submitted_documents         AS submitted,
                ecd.submission_datetime             AS submission_datetime
            FROM `tabEmployee` AS e
            JOIN `tabLMS Enrollment` AS le
                ON le.member = e.user_id
            LEFT JOIN `tabEmployee Course Documents` AS ecd
                ON ecd.employee = e.name
               AND ecd.course = le.course
               AND ecd.enrollment_version = le.enrollment_version
            WHERE e.user_id IN %(members)s
            ORDER BY e.user_id, le.enrollment_version ASC
        """
        hist_rows = frappe.db.sql(history_sql, {"members": tuple(set(members))}, as_dict=True)
        for hr in hist_rows:
            # Derive completed status if progress is 100
            progress_val = float(hr.get("progress") or 0)
            status = hr.get("completion_status") or "Pending"
            if progress_val >= 100.0 and status != "Completed":
                status = "Completed"
            entry = {
                "course": hr.get("course"),
                "enrollment_version": hr.get("enrollment_version"),
                "progress": hr.get("progress"),
                "completed_on": hr.get("completed_on"),
                "completion_status": status,
                "documents": []
            }
            if hr.get("docid"):
                entry["documents"].append({
                    "name": hr.get("docid"),
                    "docid": hr.get("docid"),
                    "submitted": bool(hr.get("submitted")),
                    "submission_datetime": hr.get("submission_datetime"),
                })
            history_by_member.setdefault(hr["member"], []).append(entry)

    # Final post-processing
    for r in data:
        # Normalize completion from progress
        try:
            prog = float(r.get("progress") or 0)
        except Exception:
            prog = 0.0
        if prog >= 100.0 and r.get("completion_status") != "Completed":
            r["completion_status"] = "Completed"
        # Attach history
        r["enrollment_history"] = history_by_member.get(r.get("employee_user_id"), [])

    return data


@frappe.whitelist(allow_guest=False, methods=["GET"])
def get_course_enrollment_cycles():
    """
    One row per LMS Enrollment cycle (every enrollment_version) of every Employee and
    Distributor, tagged with the financial year it was enrolled in and completed in, so a
    member who took a course in 2025-2026 and again in 2026-2027 shows up as two cycles.
    Read only.
    """
    from frappe.utils import flt, get_datetime
    from lms.lms.user import get_financial_year

    frappe.only_for("Supervisor")

    rows = frappe.db.sql(
        """
        SELECT
            le.name                               AS `enrollment`,
            le.member                             AS `member`,
            le.course                             AS `course`,
            c.title                               AS `course_title`,
            COALESCE(le.enrollment_version, 1)    AS `enrollment_version`,
            le.creation                           AS `enrolled_on`,
            IFNULL(le.progress, 0)                AS `progress`,
            IFNULL(le.completion_status, 'Pending') AS `completion_status`,
            le.completed_on                       AS `completed_on`,
            d.name                                AS `distributor_docid`,
            d.attendee_name                       AS `distributor_name`,
            d.account__distributor_code           AS `distributor_code`,
            d.distributor_company_name            AS `distributor_company`,
            d.country                             AS `distributor_country`,
            e.name                                AS `employee_docid`,
            e.employee_name                       AS `employee_name`,
            e.custom_employee_id                  AS `employee_code`,
            e.company                             AS `employee_company`,
            e.department                          AS `employee_department`,
            e.country                             AS `employee_country`
        FROM `tabLMS Enrollment` AS le
        LEFT JOIN `tabLMS Course` AS c
            ON c.name = le.course
        LEFT JOIN `tabDistributor` AS d
            ON d.user_id = le.member
        LEFT JOIN `tabEmployee` AS e
            ON e.user_id = le.member
        WHERE d.name IS NOT NULL OR e.name IS NOT NULL
        ORDER BY le.member, le.course, COALESCE(le.enrollment_version, 1), le.creation
        """,
        as_dict=True,
    )

    # Group the cycles of each member/course so every cycle knows its attempt number,
    # the next cycle's start and the full list of financial years.
    cycles_by_key = {}
    for r in rows:
        cycles_by_key.setdefault((r.member, r.course), []).append(r)

    data = []
    for cycles in cycles_by_key.values():
        for i, r in enumerate(cycles):
            next_start = cycles[i + 1].enrolled_on if i + 1 < len(cycles) else None
            completed_on = r.completed_on
            # Re-admission fills an empty completed_on with the re-admission time; a date
            # on or after the next cycle's start is not this cycle's completion.
            if completed_on and next_start and get_datetime(completed_on) >= get_datetime(next_start):
                completed_on = None

            progress = flt(r.progress)
            status = "Completed" if progress >= 100 else r.completion_status
            r.enrolled_fy = get_financial_year(r.enrolled_on)
            r.completed_fy = get_financial_year(completed_on) if completed_on else None
            r.completed_on = completed_on
            r.completion_status = status
            r.progress = round(progress, 2)
            r.attempt = i + 1
            r.total_attempts = len(cycles)
            r.is_current = i == len(cycles) - 1

        fy_path = []
        for r in cycles:
            if r.enrolled_fy not in fy_path:
                fy_path.append(r.enrolled_fy)

        for r in cycles:
            is_distributor = bool(r.distributor_docid)
            data.append({
                "enrollment": r.enrollment,
                "member": r.member,
                "member_type": "Distributor" if is_distributor else "Employee",
                "docid": r.distributor_docid if is_distributor else r.employee_docid,
                "member_name": (r.distributor_name if is_distributor else r.employee_name) or r.member,
                "member_code": r.distributor_code if is_distributor else r.employee_code,
                "company": r.distributor_company if is_distributor else r.employee_company,
                "department": None if is_distributor else r.employee_department,
                "country": r.distributor_country if is_distributor else r.employee_country,
                "course": r.course,
                "course_title": r.course_title or r.course,
                "enrollment_version": r.enrollment_version,
                "attempt": r.attempt,
                "total_attempts": r.total_attempts,
                "is_current": r.is_current,
                "enrolled_on": r.enrolled_on,
                "enrolled_fy": r.enrolled_fy,
                "first_enrolled_fy": fy_path[0],
                "fy_path": fy_path,
                "progress": r.progress,
                "completion_status": r.completion_status,
                "completed_on": r.completed_on,
                "completed_fy": r.completed_fy,
            })

    return data

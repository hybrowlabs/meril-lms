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
                SELECT member, MAX(enrollment_version) AS max_ev
                FROM `tabLMS Enrollment`
                GROUP BY member
            ) AS latest
            ON latest.member = le1.member AND latest.max_ev = le1.enrollment_version
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

    query = """
        SELECT
            e.name                             As `employee_docid`,
            e.employee_name                    AS `employee_name`,
            e.designation                      AS `designation`,
            e.cell_number                     AS `employee_number`,
            e.company                          AS `company`,
            e.company_email                    AS `company_email`,
            e.country                          AS `country`,
            e.custom_employee_id               AS `custom_employee_id`,
            e.user_id                          AS `employee_user_id`,
            ed.name                            AS `docuemnts_id`,
            le.course                          AS `course_name`,
        IFNULL(CAST(le.course_reminder_count AS CHAR), '0') AS `course_reminder_count`,
            le.progress                        AS `progress`,
            le.completed_on                    AS `completed_on`,
            IFNULL(le.completion_status, 'Pending') AS `completion_status`
        FROM `tabEmployee` AS e
        LEFT JOIN `tabLMS Enrollment` AS le
            ON le.member = e.user_id
        LEFT JOIN `tabEmployee Course Documents` AS ed
            ON e.name = ed.employee AND le.course = ed.course
    """
    data = frappe.db.sql(query, as_dict=True)
    return data

import frappe
import json
from frappe import _

@frappe.whitelist(allow_guest=False)
def get_distributor_dashboard_info():
    """
    Returns all distributors' info using a direct SQL query with LEFT JOIN to include
    document submission data per course, and also includes course progress, completion status,
    and course completion datetime from LMS Enrollment where course matches.

    Field names are checked against the related DocTypes for accuracy.
    LMS Enrollment fields: progress, completed_on, completion_status, member.
    """
    frappe.only_for("Supervisor")
    
    query = """
        SELECT
            d.name                               AS `distributo_docid`,
            d.attendee_name                      AS `attendee_name`,
            d.designation                        AS `designation`,
            d.user_id                            AS `distributor_user_id`,
            IFNULL(CAST(d.login_reminder_count AS CHAR), '0') AS `login_remainer_count`,
            d.distributor_email_address          AS `distributor_email_address`,
            d.distributor_contact_number         AS `distributor_contact_number`,
            d.distributor_company_name           AS `distributor_company_name`,
            d.account__distributor_code          AS `account_distributor_code`,
            d.distributor_name                   AS `distributor_name`,
            d.rsm__state_head                    AS `distributor_rsm_state_head`,
            d.bu__fd_head                        AS `distributor_bu__fd_head`,
            (
                SELECT
                    GROUP_CONCAT(CONCAT(mddc.division, ':', mddc.meril_company_name) SEPARATOR '; ')
                FROM `tabMeril Distributor Division Child` AS mddc
                WHERE mddc.parent = d.name
            ) AS `divisions_meril_company_names`,
            d.distributor_company_address        AS `distributor_company_address`,
            d.country                            AS `country`,
            d.city                               AS `city`,
            d.region                             AS `region`,
            d.state                              AS `state`,
            IFNULL(hist.enrollment_history, '[]') AS `enrollment_history`
        FROM `tabDistributor` d
        LEFT JOIN (
            SELECT
                le.member,
                JSON_ARRAYAGG(
                    JSON_OBJECT(
                        'course', le.course,
                        'progress', le.progress,
                        'completed_on', le.completed_on,
                        'completion_status', le.completion_status,
                        'enrollment_version', le.enrollment_version,
                        'documents', JSON_OBJECT(
                            'submitted', dcd.has_submitted_documents,
                            'submission_datetime', dcd.submission_datetime,
                            'docid', dcd.name
                        )
                    )
                ) AS enrollment_history
            FROM `tabLMS Enrollment` le
            LEFT JOIN `tabDistributor Course Documents` dcd
                ON dcd.distributor = (
                    SELECT name FROM `tabDistributor`
                    WHERE user_id = le.member LIMIT 1
                )
                AND dcd.course = le.course
            GROUP BY le.member
        ) hist ON hist.member = d.user_id
        ORDER BY d.distributor_name
    """
    data = frappe.db.sql(query, as_dict=True)

    # attach enrollment history JSON objects if missing
    for row in data:
        history_raw = row.pop('enrollment_history', None)
        if history_raw:
            try:
                row['enrollment_history'] = json.loads(history_raw)
            except Exception:
                row['enrollment_history'] = []
        else:
            row['enrollment_history'] = []

    return data


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

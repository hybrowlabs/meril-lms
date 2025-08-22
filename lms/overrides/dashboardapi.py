import frappe
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
            d.distributor_name                   AS `distributor_name`,
            d.distributor_contact_number         AS `distributor_contact_number`,
            d.distributor_email_address          AS `distributor_email_address`,
            d.account__distributor_code          AS `account_distributor_code`,
            d.distributor_company_address        AS `distributor_company_address`,
            d.country                            AS `country`,
            d.distributor_company_name           AS `distributor_company_name`,
            dd.has_submitted_documents           AS `submitted_documents`,
            dd.submission_datetime               AS `submission_datetime`,
            dd.name                              AS `docuemnts_id`,
            le.course                            AS `course_name`,
            le.progress                          AS `progress`,
            le.completed_on                      AS `completed_on`,
            le.completion_status                 AS `completion_status`,
           IFNULL(CAST(le.course_reminder_count AS CHAR), '0') AS `course_reminder_count`
        FROM `tabDistributor` AS d
        LEFT JOIN `tabLMS Enrollment` AS le
            ON le.member = d.user_id 
        LEFT JOIN `tabDistributor Course Documents` AS dd
            ON d.name = dd.distributor AND le.course = dd.course
    """
    data = frappe.db.sql(query, as_dict=True)
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
            e.employee_number                  AS `employee_number`,
            e.company                          AS `company`,
            e.company_email                    AS `company_email`,
            e.country                          AS `country`,
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

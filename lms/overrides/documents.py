import frappe
import random
from datetime import timedelta
from frappe.utils import now_datetime, validate_email_address, get_datetime
import base64
import unicodedata
from frappe.utils.file_manager import save_file
from docx import Document
from frappe.utils import get_fullname
import io
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import RGBColor
import base64
import unicodedata
from frappe.utils import now_datetime


@frappe.whitelist(allow_guest=False)
def has_user_submited_document(course=None):
    user = frappe.session.user
    if not course:
        return {"submited": False, "message": "No course provided"}
    
    try:
        # Check if course exists
        if not frappe.db.exists("LMS Course", course):
            return {"submited": False, "message": "Course does not exist"}

        enrollment = frappe.db.get_value("LMS Enrollment", {"course": course, "member": user}, ["name", "progress"])
        if not enrollment:
            frappe.local.response["http_status_code"] = 403
            return {
                "submited": False,
                "message": "User is not enrolled in this course"
            }
        enrollment_name, progress = enrollment
        if not progress or int(progress) < 100:
            frappe.local.response["http_status_code"] = 403
            return {
                "submited": False,
                "message": "Course progress is not completed"
            }

        user_doc = frappe.get_doc("User", user)
        roles = [role.role for role in user_doc.roles]

        documents_list = []
        distributor_id = None

        # Distributor logic
        if "Distributor" in roles:
            distributor_doc = frappe.get_doc("Distributor", {"user_id": user})
            distributor_id = distributor_doc.name

            # Check if a submitted document exists for this distributor and course
            exists = frappe.db.exists(
                "Distributor Course Documents",
                {
                    "distributor": distributor_id,
                    "course": course,
                    "has_submitted_documents": 1
                }
            )

            if not exists:
                return {"success": False, "message": "User Has not Submitted Documents"}

            documents_list = [
                "Distributor Completion Certificate",
                "Distributor Self Declaration",
                "Meril Distributor Compliance Code of Conduct",
                "Distributor Declaration - Ethical Practices & Compliance"
            ]

            # Add Endo/Non-Endo compliance policy documents based on company names
            has_endo = False
            has_non_endo = False
            for company in distributor_doc.meril_company_table:
                name = (company.meril_company_name or "").lower()
                if "endo" in name:
                    has_endo = True
                else:
                    has_non_endo = True
            if has_endo:
                documents_list.append("Meril Distributor Compliance Policy for Endo")
            if has_non_endo:
                documents_list.append("Meril Distributor Compliance Policy")

            return {
                "submited": bool(exists),
                "documents_list": documents_list,
                "course_documents_record_id": exists,
                "doctype": "Distributor Course Documents",
                "role_is": "Distributor"
            }

        # Employee logic
        elif "Employee" in roles:
            employee_doc = frappe.get_doc("Employee", {"user_id": user})
            # Check if a submitted document exists for this employee and course
            exists = frappe.db.exists(
                "Employee Course Documents",
                {"employee": employee_doc.name, "course": course}
            )
            # If 'Employee Course Documents' does not exist, create it.

            documents_list = ["Employee Declaration Form", "Employee Completion Certificate"]

            if not exists:
                employee_course_doc = frappe.get_doc({
                    "doctype": "Employee Course Documents",
                    "employee": employee_doc.name,
                    "course": course,
                })
                employee_course_doc.insert(ignore_permissions=True)
                return {
                    "submited": True,
                    "documents_list": documents_list,
                    "course_documents_record_id": employee_course_doc.name,
                    "doctype": "Employee Course Documents",
                    "role_is": "Employee"
                }

            return {
                "submited": True,
                "documents_list": documents_list,
                "course_documents_record_id": exists,
                "doctype": "Employee Course Documents",
                "role_is": "Employee"
            }

        # Other users (students, etc.)
        else:
            # Check if a submitted document exists for this user and course
            exists = frappe.db.exists(
                "User Course Documents",
                {"user": user, "course": course, "submited_document": 1}
            )
            documents_list = ["Course Completion Certificate"]
            return {
                "submited": True,
                "documents_list": documents_list,
                "doctype": "User Course Documents"
            }

    except Exception as e:
        return {"submited": False, "error": str(e)}


@frappe.whitelist(allow_guest=False)
def save_user_course_document_with_file(
    course=None,
    document_name=None,
    filename=None,
    base64_file_data=None,
    is_private=1,
    signature_type=None,
    name=None
):
    """
    Save user course document with file upload using base64 data.
    Only Distributors can upload. Only one submission per course per year is allowed.
    """

    user = frappe.session.user
    user_doc = frappe.get_doc("User", user)
    roles = [role.role for role in user_doc.roles]

    enrollment = frappe.db.get_value("LMS Enrollment", {"course": course, "member": user}, ["name", "progress"])
    if not enrollment:
        frappe.local.response["http_status_code"] = 403
        return {
            "submited": False,
            "message": "User is not enrolled in this course"
        }
    enrollment_name, progress = enrollment
    if not progress or int(progress) < 100:
        frappe.local.response["http_status_code"] = 403
        return {
            "submited": False,
            "message": "Course progress is not completed"
        }

    # Only Distributors can upload
    if "Distributor" not in roles:
        return {"success": False, "message": "User is not Distributor"}

    if not course:
        return {"success": False, "message": "No course provided"}

    if not document_name:
        return {"success": False, "message": "Document name is required"}

    if not name:
        return {"success": False, "message": "name is required"}

    if not filename or not base64_file_data:
        return {"success": False, "message": "File data is required"}

    # Debug: Log the first few characters of base64 data
    print(f"Base64 data length: {len(base64_file_data)}")
    print(f"Base64 data preview: {base64_file_data[:50]}...")

    try:
        distributor_doc = frappe.get_doc("Distributor", {"user_id": user})

        # Validate course exists
        if not frappe.db.exists("LMS Course", course):
            return {"success": False, "message": "Course not found"}

        from datetime import datetime

        # Check if a document for this distributor, course, and year exists
        existing_doc_name = frappe.db.exists(
            "Distributor Course Documents",
            {
                "distributor": distributor_doc.name,
                "course": course,
            }
        )

        doc = None
        if existing_doc_name:
            doc = frappe.get_doc("Distributor Course Documents", existing_doc_name)
            # If already submitted, do not allow another upload
            if doc.has_submitted_documents:
                return {
                    "success": False,
                    "message": "Document already submitted. You cannot upload another file for this course."
                }
        else:
            # Create new document for this distributor, course, and year
            doc = frappe.get_doc({
                "doctype": "Distributor Course Documents",
                "distributor": distributor_doc.name,
                "course": course,
                "submission_datetime": frappe.utils.now_datetime(),
                "signature_style": signature_type,
                "entered_name": name,
                "has_submitted_documents": 0
            })
            doc.insert(ignore_permissions=True)

        # Decode the base64 file data robustly
        try:
            # Clean the base64 string
            base64_file_data_clean = base64_file_data.strip()
            # Remove any non-base64 characters
            base64_file_data_clean = ''.join(
                c for c in base64_file_data_clean if c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/='
            )
            # Add padding if needed
            missing_padding = len(base64_file_data_clean) % 4
            if missing_padding:
                base64_file_data_clean += '=' * (4 - missing_padding)
            file_content = base64.b64decode(base64_file_data_clean)
        except Exception as decode_error:
            try:
                file_content = base64.urlsafe_b64decode(base64_file_data_clean)
            except Exception as url_decode_error:
                try:
                    base64_file_data_clean = base64_file_data_clean.rstrip('=')
                    missing_padding = len(base64_file_data_clean) % 4
                    if missing_padding:
                        base64_file_data_clean += '=' * (4 - missing_padding)
                    file_content = base64.b64decode(base64_file_data_clean)
                except Exception as final_error:
                    frappe.log_error(
                        f"Base64 decode failed: {str(decode_error)}, "
                        f"URL decode failed: {str(url_decode_error)}, "
                        f"Final attempt failed: {str(final_error)}"
                    )
                    return {
                        "success": False,
                        "message": "Invalid file data format. Please try uploading the file again."
                    }

        # Sanitize filename to handle special characters
        filename_ascii = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').decode('ascii')
        print("uploaded file name", filename_ascii)

        # Ensure file_content is bytes
        if not isinstance(file_content, bytes):
            file_content = file_content.encode('utf-8') if isinstance(file_content, str) else bytes(file_content)

        # Save the file using Frappe's file manager
        file_doc = save_file(
            fname=filename_ascii,
            content=file_content,
            dt="Distributor Course Documents",
            dn=doc.name,
            is_private=is_private
        )

        # Update document fields
        doc.document_name = document_name
        doc.document_file = file_doc.file_url
        doc.submission_date = now_datetime()
        doc.has_submitted_documents = 1
        if signature_type:
            doc.signature_type = signature_type

        doc.save(ignore_permissions=True)

        return {
            "success": True,
            "message": "Document saved successfully",
            "docname": doc.name,
            "file_url": file_doc.file_url,
            "file_name": file_doc.file_name
        }

    except Exception as e:
        print("File Upload error", str(e))
        frappe.log_error(f"Error saving user course document: {str(e)}")
        return {
            "success": False,
            "message": f"Error saving document: {str(e)}"
        }



@frappe.whitelist(allow_guest=True)
def generate_dynamic_docx(name=None):
    user = frappe.session.user
    user_doc = frappe.get_doc("User", user)

    if not name:
        return {
            "success": False,
            "message": "No distributor name provided"
        }

    roles = [role.role for role in user_doc.roles]
    if "Distributor" not in roles:
        return {
            "success": False,
            "message": "This document can only be generated for Distributor users."
        }

    distributor_doc = frappe.get_doc("Distributor", {"user_id": user})

    try:
        # Check for required fields and throw error if missing
        if not distributor_doc.meril_company_table or not distributor_doc.meril_company_table[0].meril_company_name:
            frappe.throw("Meril company name is missing in distributor document.")
        if not distributor_doc.distributor_company_name:
            frappe.throw("Distributor company name is missing in distributor document.")
        if not distributor_doc.attendee_name:
            frappe.throw("Attendee name is missing in distributor document.")
        if not distributor_doc.designation:
            frappe.throw("Designation is missing in distributor document.")
        if not distributor_doc.distributor_email_address and not user_doc.email:
            frappe.throw("Email address is missing in distributor and user document.")
        if not distributor_doc.distributor_contact_number and not user_doc.mobile_no:
            frappe.throw("Contact number is missing in distributor and user document.")

        meril_company_name = distributor_doc.meril_company_table[0].meril_company_name
        distributor_company_name = distributor_doc.distributor_company_name
        distributor_name = distributor_doc.attendee_name
        designation = distributor_doc.designation
        email = distributor_doc.distributor_email_address or user_doc.email
        contact_number = distributor_doc.distributor_contact_number or user_doc.mobile_no
        today = get_datetime().strftime("%d-%m-%Y")

        doc = Document()
        para = doc.add_paragraph("On letter head of distributor", style='Normal')
        para.alignment = 1
        doc.add_paragraph()
        heading = doc.add_heading("", level=1)
        run = heading.add_run("Meril Distributor- Compliance Policy Adoption Form")
        run.font.underline = True
        run.font.color.rgb = RGBColor(0, 0, 0)
        heading.alignment = 1
        doc.add_paragraph()
        doc.add_paragraph(frappe.utils.format_date(frappe.utils.nowdate(), "d MMMM yyyy"))
        doc.add_paragraph()
        doc.add_paragraph(
            f"We {distributor_company_name}, being the Distributor of Meril {meril_company_name} do hereby certify that we have willingly adopted attached Meril Distributor Compliance Policy as our own Compliance Policy with effect from {today} and declare to abide by the same.\n\n"
            "All employees, partners, directors, proprietor of our organization are expected to observe and adhere to this Policy."
        )
        doc.add_paragraph()
        doc.add_paragraph("Nomination of Compliance Officer:")
        doc.add_paragraph()
        doc.add_paragraph(
            f"{name} is nominated as Compliance Officer of our organization with effect from {frappe.utils.format_date(frappe.utils.nowdate(), 'd MMMM yyyy')}"
        )
        doc.add_paragraph()
        doc.add_paragraph(f"Authorized representative of {distributor_name}")
        doc.add_paragraph(f"Name: {distributor_name}")
        doc.add_paragraph(f"Title: {designation}")
        doc.add_paragraph(f"Email Id : {email}")
        doc.add_paragraph(f"Contact number : {contact_number}")
        doc.add_paragraph("Sign and Seal : ")

        # Save to in-memory buffer
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        # Save file to Frappe File
        file_doc = save_file(
            fname=f"{user}_compliance_policy_adoption_form.docx",
            content=buffer.getvalue(),
            dt=None,
            dn=None,
            is_private=1
        )

        return {
            "success": True,
            "file_url": file_doc.file_url,
            "file_name": file_doc.file_name
        }
    except Exception as e:
        frappe.log_error(f"Error generating dynamic docx: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def download_user_print_format_logic(document, user=None):
    """
    Internal logic for downloading a user's print format as PDF, with permission checks.
    Accepts only the document name, determines doctype and print_format, checks access, and generates the PDF.
    """
    if not user:
        user = frappe.session.user
    user_doc = frappe.get_doc("User", user)
    roles = [role.role for role in user_doc.roles]

    # Determine doctype and print_format based on document name
    if "Distributor" in document:
        doctype = "Distributor"
        # Find distributor doc for this user
        distributor = frappe.get_doc("Distributor", {"user_id": user})
        docname = distributor.name
        print_format = document
        if distributor.user_id != user:
            frappe.throw("You are not allowed to access this Distributor document.")
    elif "Employee" in document:
        doctype = "Employee"
        employee = frappe.get_doc("Employee", {"user_id": user})
        docname = employee.name
        print_format = document
        if employee.user_id != user:
            frappe.throw("You are not allowed to access this Employee document.")
    else:
        doctype = "User Course Documents"
        # Assume courseName is part of document name after a dash, or use a convention
        # Here, we expect document to be the print_format, and courseName to be passed as a param
        # For now, use the first course document for this user
        user_course_docs = frappe.get_all(
            "User Course Documents",
            filters={"user": user},
            fields=["name", "course"],
            limit_page_length=1
        )
        if not user_course_docs:
            frappe.throw("No course document found for this user.")
        docname = user_course_docs[0]["name"]
        print_format = document
        # Check access
        doc = frappe.get_doc("User Course Documents", docname)
        if doc.user != user:
            frappe.throw("You are not allowed to access this course document.")

    # Use Frappe's print format system to generate PDF
    frappe.local.flags.ignore_permissions = True
    try:
        pdf_file = frappe.get_print(
            doctype=doctype,
            name=docname,
            print_format=print_format,
            as_pdf=True,
            no_letterhead=1
        )
    finally:
        frappe.local.flags.ignore_permissions = False
    return {
        "filename": f"{doctype}-{docname}.pdf",
        "filecontent": pdf_file,
        "type": "pdf"
    }


@frappe.whitelist(allow_guest=False)
def get_distributor_print_format_info(course):
    """
    Returns the correct doctype and document name for distributor print formats.
    Some print formats are for 'Distributor' doctype, others for 'Distributor Course Documents'.
    """
    user = frappe.session.user
    user_doc = frappe.get_doc("User", user)
    roles = [role.role for role in user_doc.roles]
    
    try:
        if "Distributor" in roles:
            distributor_name = frappe.get_value("Distributor", {"user_id": user}, "name")
            document_id = frappe.get_doc("Distributor Course Documents", {"distributor": distributor_name, "course": course})
            return {
                "success": True,
               "document_id" : document_id ,
               "doctype": "Distributor Course Documents"
            }
        elif "Employee" in roles:
            employee_name = frappe.get_value("Employee", {"user_id": user}, "name")
            document_id = frappe.get_doc("Employee Course Documents", {"employee": employee_name, "course": course})
            return {
                "success": True,
                "document_id" : document_id,
                "doctype": "Employee Course Documents"
            }
        else:
            return {
                "success": False,
                "message": f"Unknown document id for course: {course}"
            }
            
    except Exception as e:
        frappe.log_error(f"Error in get_distributor_print_format_info: {str(e)}")
        return {
            "success": False,
            "message": f"Error getting document info: {str(e)}"
        }


@frappe.whitelist(allow_guest=False)
def get_public_signature_font_styles():
    """
    Returns a list of available signature font styles (Signature Type doctype)
    where the font file is not private (i.e., not in /private/files/).
    """
    try:
        font_types = frappe.get_all(
            "Signature Type",
            filters={
                "font_file": ["not like", "/private/files/%"]
            },
            fields=["name", "font_name", "font_file"]
        )
        # Optionally, add a 'label' and 'value' for frontend select
        result = []
        for font in font_types:
            result.append({
                "label": font.get("font_name") or font.get("name"),
                "value": font.get("name"),
                "css": font.get("font_name"),  # Assuming font_name is the CSS font-family
                "font_file": font.get("font_file")
            })
        return result
    except Exception as e:
        frappe.log_error(f"Error fetching public signature font styles: {str(e)}")
        return []

@frappe.whitelist(allow_guest=False)
def downlaod_nonendo_file():
    from frappe.utils.file_manager import get_file_path
    user = frappe.session.user

    # Check if user has Distributor role
    user_doc = frappe.get_doc("User", user)
    roles = [role.role for role in user_doc.roles]
    if "Distributor" not in roles:
        frappe.local.response["http_status_code"] = 403
        frappe.local.response["message"] = "Only Distributor can download this file"
        return

    # Try to get Distributor doc by user_id (not by name, which is not always user email)
    distributor_doc = frappe.get_doc("Distributor", {"user_id": user}, ignore_permissions=True)
    if not distributor_doc:
        frappe.local.response["http_status_code"] = 403
        frappe.local.response["message"] = "Distributor record not found"
        return

    # Check if any company name does NOT contain "endo" (case-insensitive)
    for company in distributor_doc.meril_company_table:
        name = (company.meril_company_name or "").lower()
        if "endo" not in name:
            # Use the direct file path as requested
            file_docname = frappe.db.get_value("File", {"file_name": "Meril Distributor Compliance policy.pdf"})
            if not file_docname:
                frappe.local.response["http_status_code"] = 404
                frappe.local.response["message"] = "File not found"
                return

            file_doc = frappe.get_doc("File", file_docname)
            file_path = get_file_path(file_doc.file_url)

            with open(file_path, "rb") as f:
                file_content = f.read()

            # Set response headers for file download
            frappe.response["type"] = "binary"
            frappe.response["filename"] = file_doc.file_name
            frappe.response["filecontent"] = file_content
            return

    frappe.local.response["http_status_code"] = 403
    frappe.local.response["message"] = "Distributor can not access this resource"
    return

@frappe.whitelist(allow_guest=False)
def downlaod_endo_file():
    from frappe.utils.file_manager import get_file_path
    user = frappe.session.user

    # Check if user has Distributor role
    user_doc = frappe.get_doc("User", user)
    roles = [role.role for role in user_doc.roles]
    if "Distributor" not in roles:
        frappe.local.response["http_status_code"] = 403
        frappe.local.response["message"] = "Only Distributor can download this file"
        return

    # Try to get Distributor doc by user_id (not by name, which is not always user email)
    distributor_doc = frappe.get_doc("Distributor", {"user_id": user}, ignore_permissions=True)
    if not distributor_doc:
        frappe.local.response["http_status_code"] = 403
        frappe.local.response["message"] = "Distributor record not found"
        return

    # Check if any company name contains "endo" (case-insensitive)
    for company in distributor_doc.meril_company_table:
        name = (company.meril_company_name or "").lower()
        if "endo" in name:
            # Use the direct file path as requested
            file_docname = frappe.db.get_value("File", {"file_name": "Meril Distributor Compliance policy for Endo.pdf"})
            if not file_docname:
                frappe.local.response["http_status_code"] = 404
                frappe.local.response["message"] = "File not found"
                return

            file_doc = frappe.get_doc("File", file_docname)
            file_path = get_file_path(file_doc.file_url)

            with open(file_path, "rb") as f:
                file_content = f.read()

            # Set response headers for file download
            frappe.response["type"] = "binary"
            frappe.response["filename"] = file_doc.file_name
            frappe.response["filecontent"] = file_content
            return

    frappe.local.response["http_status_code"] = 403
    frappe.local.response["message"] = "Distributor can not access this resource"
    return
import frappe
import random
from datetime import timedelta
from frappe.utils import now_datetime, validate_email_address, get_datetime
import base64
import unicodedata
from frappe.utils.file_manager import save_file
from frappe.utils import get_fullname
import io
from docx import Document
from docx.shared import RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from PIL import Image, ImageDraw, ImageFont, ImageChops
import requests
from frappe.utils.file_manager import get_file_path

@frappe.whitelist(allow_guest=False)
def get_next_distributor_document(course=None):
    """
    Returns the next document name that the distributor needs to upload for the given course,
    based on the enabled flags and what has already been submitted.
    """
    user = frappe.session.user
    if not course:
        return {"success": False, "message": "No course provided"}

    # Check if course exists
    if not frappe.db.exists("LMS Course", course):
        return {"success": False, "message": "Course does not exist"}

    # Get user roles
    user_doc = frappe.get_doc("User", user)
    roles = [role.role for role in user_doc.roles]

    # Only for Distributors
    if "Distributor" not in roles:
        return {"success": False, "message": "User is not a Distributor"}

    # Get distributor doc
    distributor_doc = frappe.get_doc("Distributor", {"user_id": user})
    distributor_id = distributor_doc.name

    # Get enabled document flags for this course/distributor
    # This logic should match the frontend's "priority" order
    # For now, assume a function exists to get these flags (or hardcode for demo)
    # You may want to replace this with your own logic as needed
    enabled_flags = frappe.call("lms.overrides.documents.get_upload_download_docuemtn_enabled", course=course)
    # Fallback if not callable
    if not enabled_flags or not enabled_flags.get("success", True):
        # fallback: try to get from course or system settings
        enabled_flags = {
            "distributor_self_declaration": True,
            "meril_distributor_compliance_code_of_conduct": True,
            "meril_distributor_compliance_policy_adoption_form": True,
        }

    # List of document names in priority order (should match frontend)
    doc_priority = [
        ("meril_distributor_compliance_policy_adoption_form", "Meril Distributor Compliance Policy Adoption Form"),
        ("distributor_self_declaration", "Distributor Self Declaration"),
        ("meril_distributor_compliance_code_of_conduct", "Meril Distributor Compliance Code of Conduct")
    ]

    # Get already submitted documents for this distributor and course
    # Check child table for uploaded documents
    existing_doc = frappe.db.exists(
        "Distributor Course Documents",
        {"distributor": distributor_id, "course": course}
    )

    submitted_names = set()
    if existing_doc:
        doc = frappe.get_doc("Distributor Course Documents", existing_doc)
        # Check child table for uploaded documents
        if doc.document_upload_datetime:
            for upload in doc.document_upload_datetime:
                doc_name = getattr(upload, 'document', None) or getattr(upload, 'document_name', None)
                if doc_name:
                    submitted_names.add(doc_name)

    # Find the next document that is enabled and not yet submitted
    for flag, doc_name in doc_priority:
        if enabled_flags.get(flag) and doc_name not in submitted_names:
            return {
                "success": True,
                "next_document": doc_name
            }

    # If all enabled documents are already submitted
    return {
        "success": True,
        "next_document": None,
        "message": "All required documents have been submitted"
    }


@frappe.whitelist(allow_guest=False)
def has_user_submited_document(course=None):
    user = frappe.session.user
    if not course:
        return {"submited": False, "message": "No course provided", "success": False}

    try:
        # Check if course exists
        if not frappe.db.exists("LMS Course", course):
            return {"submited": False, "message": "Course does not exist", "success": False}

        enrollment = frappe.db.get_value("LMS Enrollment", {"course": course, "member": user}, ["name", "progress"])
        if not enrollment:
            # Don't set 403 status, just return the data
            return {
                "submited": False,
                "message": "User is not enrolled in this course",
                "success": False,
                "enrollment_required": True
            }
        enrollment_name, progress = enrollment
        if not progress or int(progress) < 100:
            # Don't set 403 status, just return the data
            return {
                "submited": False,
                "message": "Course progress is not completed",
                "success": False,
                "progress": progress or 0
            }

        # Auto-create Distributor Course Documents when course is completed
        create_course_documents_on_completion(user, course, enrollment_name)

        user_doc = frappe.get_doc("User", user)
        roles = [role.role for role in user_doc.roles]

        documents_list = []
        distributor_id = None

        # Distributor logic
        if "Distributor" in roles:
            distributor_doc = frappe.get_doc("Distributor", {"user_id": user})
            distributor_id = distributor_doc.name

            # Check if a document record exists for this distributor and course
            # First check for submitted documents
            submitted_exists = frappe.db.exists(
                "Distributor Course Documents",
                {
                    "distributor": distributor_id,
                    "course": course,
                    "has_submitted_documents": 1
                }
            )

            # Also check for any document record (even partial uploads)
            any_exists = frappe.db.exists(
                "Distributor Course Documents",
                {
                    "distributor": distributor_id,
                    "course": course
                }
            )

            # Get uploaded documents if any record exists
            uploaded_documents = []
            if any_exists:
                doc = frappe.get_doc("Distributor Course Documents", any_exists)
                if doc.document_upload_datetime:
                    for upload in doc.document_upload_datetime:
                        doc_name = getattr(upload, 'document', None) or getattr(upload, 'document_name', None)
                        if doc_name:
                            # Get the file attachment details (note the typo in field name)
                            file_url = getattr(upload, 'uploaded_docuement', None) or getattr(upload, 'uploaded_document', None) or getattr(upload, 'upload_document', None)
                            uploaded_documents.append({
                                "name": doc_name,
                                "upload_datetime": str(upload.upload_datetime) if upload.upload_datetime else None,
                                "file_url": file_url
                            })

            # Build documents_list (static downloads available regardless of submission)
            documents_list = [
                "Distributor Completion Certificate",
                "Distributor Self Declaration",
                "Meril Distributor Compliance Code of Conduct"
            ]

            # Add Endo/Non-Endo compliance policy documents based on company names
            has_endo = False
            has_non_endo = False
            for company in distributor_doc.meril_company_table:
                name = (company.division or "").lower()
                if "endo" in name:
                    has_endo = True
                else:
                    has_non_endo = True
            if has_endo:
                documents_list.append("Meril Distributor Compliance Policy for Endo")
            if has_non_endo:
                documents_list.append("Meril Distributor Compliance Policy")

            if not submitted_exists:
                return {
                    "submited": False,  # Important: frontend checks this field
                    "success": True,  # Changed to True to avoid error handling
                    "message": "User Has not Submitted Documents",
                    "role_is": "Distributor",
                    "uploaded_documents": uploaded_documents,
                    "course_documents_record_id": any_exists,
                    "documents_list": documents_list,
                    "doctype": "Distributor Course Documents"
                }

            return {
                "submited": bool(submitted_exists),
                "success": True,
                "documents_list": documents_list,
                "uploaded_documents": uploaded_documents,
                "course_documents_record_id": submitted_exists or any_exists,
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
                return {
                    "submited": False,
                    "success": True,
                    "documents_list": documents_list,
                    "course_documents_record_id": None,
                    "doctype": "Employee Course Documents",
                    "role_is": "Employee"
                }

            return {
                "submited": True,
                "success": True,
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
                "success": True,
                "documents_list": documents_list,
                "doctype": "User Course Documents"
            }

    except Exception as e:
        frappe.log_error(f"Error in has_user_submited_document: {str(e)}")
        return {
            "submited": False,
            "success": False,
            "error": str(e),
            "message": "An error occurred while checking document status"
        }


def create_course_documents_on_completion(user=None, course=None, enrollment_name=None):
    """
    Automatically create Distributor/Employee Course Documents when course reaches 100% completion.
    This ensures print formats are available immediately after course completion.
    """
    if not user:
        user = frappe.session.user

    if not course:
        return {"success": False, "message": "No course provided"}

    try:
        user_doc = frappe.get_doc("User", user)
        roles = [role.role for role in user_doc.roles]

        # Handle Distributor
        if "Distributor" in roles:
            distributor_doc = frappe.get_doc("Distributor", {"user_id": user})

            # Check if document already exists
            existing = frappe.db.exists(
                "Distributor Course Documents",
                {"distributor": distributor_doc.name, "course": course}
            )

            doc = None
            if existing:
                # Document exists, check if completion certificate is already in child table
                doc = frappe.get_doc("Distributor Course Documents", existing)

                # Check if completion certificate already exists in child table
                has_certificate = False
                if doc.document_upload_datetime:
                    for upload in doc.document_upload_datetime:
                        if upload.document == "Distributor Completion Certificate":
                            has_certificate = True
                            break

                # If certificate doesn't exist, generate and add it
                if not has_certificate:
                    try:
                        # Generate PDF from print format
                        pdf_content = frappe.get_print(
                            doctype="Distributor Course Documents",
                            name=doc.name,
                            print_format="Distributor Completion Certificate",
                            as_pdf=True,
                            no_letterhead=1
                        )

                        # Save the PDF as a file attachment
                        file_doc = save_file(
                            fname="Distributor_Completion_Certificate.pdf",
                            content=pdf_content,
                            dt="Distributor Course Documents",
                            dn=doc.name,
                            is_private=0  # Making it not private so it can be downloaded
                        )

                        # Add the certificate to the child table
                        if not getattr(doc, "document_upload_datetime", None):
                            doc.set("document_upload_datetime", [])

                        # First check if the document type exists, if not create it
                        if not frappe.db.exists("Distributor Document Type", "Distributor Completion Certificate"):
                            cert_type = frappe.get_doc({
                                "doctype": "Distributor Document Type",
                                "name1": "Distributor Completion Certificate"
                            })
                            cert_type.insert(ignore_permissions=True)

                        # Append the completion certificate to child table
                        child = doc.append(
                            "document_upload_datetime",
                            {
                                "upload_datetime": frappe.utils.now_datetime(),
                                "document": "Distributor Completion Certificate",
                                "uploaded_docuement": file_doc.file_url  # Note the typo in field name
                            }
                        )
                        doc.save(ignore_permissions=True)
                        frappe.db.commit()

                    except Exception as e:
                        frappe.log_error(f"Error generating completion certificate for existing distributor doc: {str(e)}")

            else:
                # Create new Distributor Course Documents
                doc = frappe.get_doc({
                    "doctype": "Distributor Course Documents",
                    "distributor": distributor_doc.name,
                    "course": course,
                    "has_submitted_documents": 0,
                    "submission_date": frappe.utils.now_datetime(),
                    "entered_name": distributor_doc.attendee_name or user_doc.full_name or ""
                })
                doc.insert(ignore_permissions=True)

                # Generate and attach the completion certificate PDF
                try:
                    # Generate PDF from print format
                    pdf_content = frappe.get_print(
                        doctype="Distributor Course Documents",
                        name=doc.name,
                        print_format="Distributor Completion Certificate",
                        as_pdf=True,
                        no_letterhead=1
                    )

                    # Save the PDF as a file attachment
                    file_doc = save_file(
                        fname="Distributor_Completion_Certificate.pdf",
                        content=pdf_content,
                        dt="Distributor Course Documents",
                        dn=doc.name,
                        is_private=0  # Making it not private so it can be downloaded
                    )

                    # Add the certificate to the child table
                    if not getattr(doc, "document_upload_datetime", None):
                        doc.set("document_upload_datetime", [])

                    # First check if the document type exists, if not create it
                    if not frappe.db.exists("Distributor Document Type", "Distributor Completion Certificate"):
                        cert_type = frappe.get_doc({
                            "doctype": "Distributor Document Type",
                            "name1": "Distributor Completion Certificate"
                        })
                        cert_type.insert(ignore_permissions=True)

                    # Append the completion certificate to child table
                    child = doc.append(
                        "document_upload_datetime",
                        {
                            "upload_datetime": frappe.utils.now_datetime(),
                            "document": "Distributor Completion Certificate",
                            "uploaded_docuement": file_doc.file_url  # Note the typo in field name
                        }
                    )
                    doc.save(ignore_permissions=True)

                except Exception as e:
                    frappe.log_error(f"Error generating completion certificate for distributor: {str(e)}")
                    # Continue even if certificate generation fails

                frappe.db.commit()

                return {
                    "success": True,
                    "message": "Distributor Course Documents created",
                    "doc_name": doc.name
                }

        # Handle Employee
        elif "Employee" in roles:
            employee_doc = frappe.get_doc("Employee", {"user_id": user})

            # Check if document already exists
            existing = frappe.db.exists(
                "Employee Course Documents",
                {"employee": employee_doc.name, "course": course}
            )

            if not existing:
                # Create new Employee Course Documents
                doc = frappe.get_doc({
                    "doctype": "Employee Course Documents",
                    "employee": employee_doc.name,
                    "course": course,
                    "submission_date": frappe.utils.now_datetime()
                })
                doc.insert(ignore_permissions=True)
                frappe.db.commit()

                return {
                    "success": True,
                    "message": "Employee Course Documents created",
                    "doc_name": doc.name
                }

        return {"success": True, "message": "Documents already exist or not applicable"}

    except Exception as e:
        frappe.log_error(f"Error creating course documents on completion: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist(allow_guest=False)
def upload_distributor_document_with_datetime(
    course=None,
    document_name=None,
    filename=None,
    base64_file_data=None,
    is_private=1,
    signature_type=None,
    name=None,
    document_upload_datetime=None,
    uploadDocumentName=None
):
    """
    Upload a distributor document for the Distributor Course Documents doctype,
    and record the upload datetime in the document_upload_datetime child table.
    Ensures the file is actually attached to an inserted parent document.
    """
    try:
        user = frappe.session.user
        user_doc = frappe.get_doc("User", user)
        roles = [role.role for role in user_doc.roles]

        # Only Distributors can upload
        if "Distributor" not in roles:
            return {"success": False, "message": "User is not Distributor"}

        if not course:
            return {"success": False, "message": "No course provided"}

        if not document_name:
            return {"success": False, "message": "Document name is required"}

        if not filename or not base64_file_data:
            return {"success": False, "message": "File data is required"}

        # Check that uploadDocumentName is a valid document type
        if not uploadDocumentName:
            return {"success": False, "message": "Document type (uploadDocumentName) is required."}
        valid_types = [
            "Meril Distributor Compliance Policy Adoption Form",
            "Distributor Self Declaration",
            "Meril Distributor Compliance Code of Conduct"
        ]
        if uploadDocumentName not in valid_types:
            # Try to get from DocType if the hardcoded list fails
            try:
                db_types = frappe.get_all("Distributor Document Type", pluck="name")
                if uploadDocumentName not in db_types:
                    return {
                        "success": False,
                        "message": f"Invalid document type: {uploadDocumentName}. Allowed types: {', '.join(valid_types)}"
                    }
            except:
                if uploadDocumentName not in valid_types:
                    return {
                        "success": False,
                        "message": f"Invalid document type: {uploadDocumentName}. Allowed types: {', '.join(valid_types)}"
                    }
        # Validate allowed extensions
        allowed_ext = (".doc", ".docx", ".pdf")
        if not filename.lower().endswith(allowed_ext):
            return {"success": False, "message": "Only .doc, .docx, or .pdf files are allowed"}

        # Validate enrollment and completion
        enrollment = frappe.db.get_value("LMS Enrollment", {"course": course, "member": user}, ["name", "progress"])
        if not enrollment:
            # Don't set 403 status, just return error data
            return {"success": False, "message": "User is not enrolled in this course", "enrollment_required": True}
        _, progress = enrollment
        if not progress or int(progress) < 100:
            # Don't set 403 status, just return error data
            return {"success": False, "message": "Course progress is not completed", "progress": progress or 0}

        # Parent Distributor Course Documents – reuse if exists for this course, else create
        distributor_doc = frappe.get_doc("Distributor", {"user_id": user})
        existing_name = frappe.db.exists(
            "Distributor Course Documents",
            {"distributor": distributor_doc.name, "course": course}
        )
        if existing_name:
            doc = frappe.get_doc("Distributor Course Documents", existing_name)
        else:
            doc = frappe.get_doc({
                "doctype": "Distributor Course Documents",
                "distributor": distributor_doc.name,
                "course": course,
                "has_submitted_documents": 0,
            })
            doc.insert(ignore_permissions=True)

        # Decode base64 safely
        import base64, unicodedata
        try:
            base64_file_data_clean = (base64_file_data or "").strip().replace("\n", "").replace("\r", "")
            missing_padding = len(base64_file_data_clean) % 4
            if missing_padding:
                base64_file_data_clean += "=" * (4 - missing_padding)
            file_content = base64.b64decode(base64_file_data_clean)
        except Exception as e:
            frappe.log_error(f"Base64 decode failed: {str(e)}")
            return {"success": False, "message": "Invalid file data format. Please try uploading the file again."}

        # Sanitize filename
        filename_ascii = unicodedata.normalize("NFKD", filename).encode("ascii", "ignore").decode("ascii")

        # Update parent with metadata (no file attachment on parent)
        doc.document_name = document_name
        doc.submission_date = now_datetime()
        if signature_type:
            # keep field name flexible if present on doctype
            if hasattr(doc, "signature_type"):
                doc.signature_type = signature_type
            elif hasattr(doc, "signature_style"):
                doc.signature_style = signature_type
        if name and hasattr(doc, "entered_name"):
            doc.entered_name = name

        # Append upload record in child table with document name, datetime, and file link
        try:
            # Normalize incoming ISO datetime (e.g., 2025-09-23T13:44:12.991Z) to MySQL-friendly
            normalized_dt = None
            if document_upload_datetime:
                try:
                    s = str(document_upload_datetime).strip()
                    # Replace T with space, drop trailing Z, limit to seconds if needed
                    s = s.replace('T', ' ').replace('Z', '')
                    # Trim fractional seconds to microseconds supported by MySQL if present
                    if '.' in s:
                        main, frac = s.split('.', 1)
                        # keep up to 6 digits
                        frac = ''.join(ch for ch in frac if ch.isdigit())[:6]
                        s = main + ('.' + frac if frac else '')
                    normalized_dt = get_datetime(s)
                except Exception:
                    normalized_dt = now_datetime()
            else:
                normalized_dt = now_datetime()

            if not getattr(doc, "document_upload_datetime", None):
                doc.set("document_upload_datetime", [])
            # Create child row first, save parent, then attach file to PARENT doctype
            child = doc.append(
                "document_upload_datetime",
                {
                    "upload_datetime": normalized_dt,
                    # Save name to the correct field in child schema
                    "document": uploadDocumentName,  # This is the Link field to Distributor Document Type
                },
            )
            doc.save(ignore_permissions=True)
            # Attach file to parent doctype (standard file attachment)
            file_doc = save_file(
                fname=filename_ascii,
                content=file_content,
                dt="Distributor Course Documents",
                dn=doc.name,
                is_private=int(is_private) if is_private is not None else 1,
            )
            # persist file url on child row field (note the typo in the field name)
            if hasattr(child, "uploaded_docuement"):  # Note: field has typo
                child.uploaded_docuement = file_doc.file_url
            elif hasattr(child, "uploaded_document"):
                child.uploaded_document = file_doc.file_url
            elif hasattr(child, "upload_document"):
                child.upload_document = file_doc.file_url
            child.save(ignore_permissions=True)
        except Exception:
            # fail-soft if child table not configured
            pass

        # Conditionally mark as submitted only when all enabled docs are uploaded
        try:
            lms_settings = frappe.get_single("LMS Settings")
            # Build the list of required document names based on enabled settings
            required_docs = []
            if getattr(lms_settings, "meril_distributor_compliance_policy_adoption_form", False):
                required_docs.append("Meril Distributor Compliance Policy Adoption Form")
            if getattr(lms_settings, "distributor_self_declaration", False):
                required_docs.append("Distributor Self Declaration")
            if getattr(lms_settings, "meril_distributor_compliance_code_of_conduct", False):
                required_docs.append("Meril Distributor Compliance Code of Conduct")
            # No 4th document needed - only 3 documents are uploaded by user

            # Gather all uploaded document names from the child table
            uploaded_names = set()
            for row in (getattr(doc, "document_upload_datetime", []) or []):
                docname = getattr(row, "document", None) or getattr(row, "document_name", None)
                if docname:
                    uploaded_names.add(docname)

            # Mark as submitted only if all required docs are present in uploaded_names
            # We expect 3 or 4 documents (depending on settings), NOT including completion certificate
            if required_docs and all(req in uploaded_names for req in required_docs):
                doc.has_submitted_documents = 1
            else:
                doc.has_submitted_documents = 0

        except Exception:
            # If settings or child table missing, do not force submission flag
            pass
        doc.save(ignore_permissions=True)

        # Suggest next document to upload, if any
        next_info = {}
        try:
            next_info = get_next_distributor_document(course)
        except Exception:
            next_info = {}

        return {
            "success": True,
            "message": "Document uploaded successfully",
            "docname": doc.name,
            "file_url": file_doc.file_url,
            "file_name": file_doc.file_name,
            "next_document": next_info.get("next_document") if isinstance(next_info, dict) else None,
        }

    except Exception as e:
        frappe.log_error(f"Error uploading distributor document: {str(e)}")
        return {"success": False, "message": f"Error uploading document: {str(e)}"}


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
        # Don't set 403 status, just return error data
        return {
            "success": False,
            "submited": False,
            "message": "User is not enrolled in this course"
        }
    enrollment_name, progress = enrollment
    if not progress or int(progress) < 100:
        # Don't set 403 status, just return error data
        return {
            "success": False,
            "submited": False,
            "message": "Course progress is not completed",
            "progress": progress or 0
        }

    # Only Distributors can upload
    if "Distributor" not in roles:
        return {"success": False, "message": "User is not Distributor"}

    if not course:
        return {"success": False, "message": "No course provided"}

    if not document_name:
        return {"success": False, "message": "Document name is required"}


    if not filename or not base64_file_data:
        return {"success": False, "message": "File data is required"}

    # Check that filename is only .doc, .docx, or .pdf (case-insensitive)
    allowed_extensions = [".doc", ".docx", ".pdf"]
    if not any(filename.lower().endswith(ext) for ext in allowed_extensions):
        return {
            "success": False,
            "message": "Only MS Word (.doc, .docx) or PDF (.pdf) files are allowed."
        }
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
            is_private=1
        )

        # Update document fields
        doc.document_name = document_name
        doc.document_file = file_doc.file_url
        doc.submission_date = now_datetime()
    
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

def trim_img_whitespace(img):
    """Crop extra white/transparent space around text."""
    # Use a white background for RGB, transparent for RGBA
    if img.mode == "RGBA":
        bg = Image.new("RGBA", img.size, (255, 255, 255, 0))
    else:
        bg = Image.new(img.mode, img.size, (255, 255, 255))
    diff = ImageChops.difference(img, bg)
    bbox = diff.getbbox()
    if bbox:
        return img.crop(bbox)
    return img

def get_signature_image(
    text="Signature",
    font_path=None,
    font_size=25,      
    fixed_height=25,    
    dpi=300,            
):

    if not font_path:
        font_path = "/assets/lms/fonts/signature/BantengStory.otf"

    font_path = font_path.lstrip("/")
    base_url = frappe.utils.get_url()
    font_url = f"{base_url}/{font_path}"

    try:
        response = requests.get(font_url)
        response.raise_for_status()
        font_bytes = io.BytesIO(response.content)
        # PIL expects font size in points, but at 300dpi, 12pt = 50px
        # 1pt = 1/72 inch, so at 300dpi: px = pt * 300 / 72
        pil_font_size = int(font_size * dpi / 72)
        font = ImageFont.truetype(font_bytes, pil_font_size)
    except Exception as e:
        print(f"Font '{font_url}' could not be loaded: {e}. Using default.")
        font = ImageFont.load_default()
        pil_font_size = font_size

    # Get font metrics (ascent + descent)
    ascent, descent = font.getmetrics()

    # Measure text
    dummy_img = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(dummy_img)
    text_bbox = draw.textbbox((0, 0), text, font=font)

    text_w = text_bbox[2] - text_bbox[0]
    text_h = ascent + descent  # more accurate than bbox for full font height

    # Add padding
    pad = int(pil_font_size * 0.2)  # Padding relative to font size
    img_w = text_w + pad * 2
    img_h = text_h + pad * 2

    # Create image
    img = Image.new("RGBA", (img_w, img_h), (255, 255, 255, 0))
    d = ImageDraw.Draw(img)

    # Draw text so that full ascent+descent fits
    text_x = pad
    text_y = pad
    d.text((text_x, text_y), text, font=font, fill=(0, 0, 0, 255))

    img = trim_img_whitespace(img)

    # Always set image to fixed height, width adjusts to keep aspect ratio
    if img.height != fixed_height:
        aspect_ratio = img.width / img.height
        new_width = int(fixed_height * aspect_ratio)
        img = img.resize((new_width, fixed_height), Image.LANCZOS)

    # Save to memory with high DPI for better quality in docx
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG", dpi=(dpi, dpi))
    img_bytes.seek(0)
    return img_bytes

@frappe.whitelist(allow_guest=True)
def get_upload_download_docuemtn_enabled():
    """
    Returns the boolean values of three check fields from LMS Settings:
    - distributor_self_declaration
    - meril_distributor_compliance_code_of_conduct
    - meril_distributor_compliance_policy_adoption_form

    Returns:
        dict: {
            "distributor_self_declaration": bool,
            "meril_distributor_compliance_code_of_conduct": bool,
            "meril_distributor_compliance_policy_adoption_form": bool
        }
    """
    user = frappe.session.user
    if not user or user == "Guest":
        return {
            "success": False,
            "message": "User not logged in."
        }

    # Fetch from LMS Settings doctype (assume singleton)
    lms_settings = frappe.get_single("LMS Settings")

    if not lms_settings:
        return {
            "success": False,
            "message": "LMS Settings not found."
        }

    return {
        "success": True,
        "distributor_self_declaration": bool(getattr(lms_settings, "distributor_self_declaration", False)),
        "meril_distributor_compliance_code_of_conduct": bool(getattr(lms_settings, "meril_distributor_compliance_code_of_conduct", False)),
        "meril_distributor_compliance_policy_adoption_form": bool(getattr(lms_settings, "meril_distributor_compliance_policy_adoption_form", False))
    }


@frappe.whitelist(allow_guest=False)
def get_next_distributor_document_after_upload(course: str | None = None):
    """
    After a successful upload (e.g. Code of Conduct), decide which distributor document
    should be prompted next based on LMS Settings flags and distributor company context.

    Priority for NEXT doc:
      - If Policy Adoption is enabled → return appropriate policy doc (Endo/Non-Endo/both)
      - Otherwise → return None
    """
    user = frappe.session.user
    if not course:
        return {"success": False, "message": "No course provided"}

    # Ensure user is Distributor and enrolled
    enrollment = frappe.db.get_value("LMS Enrollment", {"course": course, "member": user}, ["name", "progress"])
    if not enrollment:
        frappe.local.response["http_status_code"] = 403
        return {"success": False, "message": "User is not enrolled in this course"}

    user_doc = frappe.get_doc("User", user)
    roles = [r.role for r in user_doc.roles]
    if "Distributor" not in roles:
        return {"success": False, "message": "Only Distributor flow supported"}

    flags = get_upload_download_docuemtn_enabled()
    if not flags.get("success"):
        return {"success": False, "message": "Unable to read LMS Settings"}

    # Next: Only the three LMS Settings-controlled documents are considered.
    # After Code of Conduct, prompt Policy Adoption Form if enabled.
    if flags.get("meril_distributor_compliance_policy_adoption_form"):
        return {
            "success": True,
            "next_document": "Meril Distributor Compliance Policy Adoption Form",
        }

    return {"success": True, "next_document": None}

@frappe.whitelist(allow_guest=False)
def generate_dynamic_docx(name=None, font_path=None, course=None, use_print_format=False, document_type=None):
    """
    Generate either a DOCX with signature or PDF using print format based on parameters.
    If use_print_format is True or course is provided, generate PDF from print format.
    Otherwise, generate DOCX with signature (backward compatibility).
    document_type: The type of document to generate (e.g., 'Meril Distributor Compliance Policy Adoption Form')
    """
    from docx.shared import Inches, Pt
    import base64
    from frappe.utils import now_datetime

    user = frappe.session.user
    user_doc = frappe.get_doc("User", user)

    if not name:
        return {
            "success": False,
            "message": "No compliance officer name provided"
        }

    roles = [role.role for role in user_doc.roles]
    if "Distributor" not in roles:
        return {
            "success": False,
            "message": "This document can only be generated for Distributor users."
        }

    distributor_doc = frappe.get_doc("Distributor", {"user_id": user})

    # If course is provided, generate PDF using print format
    if course or use_print_format:
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

            # Get or create Distributor Course Documents record
            doc_name = None
            if course:
                doc_name = frappe.db.exists(
                    "Distributor Course Documents",
                    {"distributor": distributor_doc.name, "course": course}
                )

            if doc_name:
                doc = frappe.get_doc("Distributor Course Documents", doc_name)
            elif course:
                doc = frappe.get_doc({
                    "doctype": "Distributor Course Documents",
                    "distributor": distributor_doc.name,
                    "course": course,
                    "has_submitted_documents": 0
                })
                doc.insert(ignore_permissions=True)
            else:
                # Create a temporary document for print format generation
                doc = frappe.get_doc({
                    "doctype": "Distributor Course Documents",
                    "distributor": distributor_doc.name,
                    "course": "",
                    "has_submitted_documents": 0,
                    "entered_name": name,
                    "submission_datetime": now_datetime()
                })
                # Don't save temporary document
                doc.name = "temp-" + frappe.generate_hash(length=10)

            # Update the entered_name field with the compliance officer name
            doc.entered_name = name
            doc.submission_datetime = now_datetime()
            if course:  # Only save if course is provided
                doc.save(ignore_permissions=True)

            # Determine which print format to use based on document_type
            print_format_name = document_type or "Meril Distributor Compliance Policy Adoption Form"

            # Generate PDF using the print format
            pdf_content = frappe.get_print(
                doctype="Distributor Course Documents",
                name=doc.name if course else None,
                doc=doc if not course else None,  # Pass doc object if temporary
                print_format=print_format_name,
                as_pdf=True,
                no_letterhead=1
            )

            pdf_content_base64 = base64.b64encode(pdf_content).decode('utf-8')

            # Generate appropriate filename based on document type
            file_name = (document_type or "Meril_Distributor_Compliance_Policy_Adoption_Form").replace(" ", "_") + ".pdf"

            return {
                "success": True,
                "file_content": pdf_content_base64,
                "file_name": file_name,
                "document_id": doc.name if course else None
            }
        except Exception as e:
            frappe.log_error(f"Error generating PDF from print format: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    # Original DOCX generation with signature
    if font_path is None:
        return {
            "success": False,
            "message": "No Signature Style Selected"
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
    user = frappe.session.user

    # Check if user has Distributor role
    user_doc = frappe.get_doc("User", user)
    roles = [role.role for role in user_doc.roles]
    if "Distributor" not in roles:
        frappe.local.response["message"] = "Only Distributor can download this file"
        frappe.local.response["http_status_code"] = 200  # Return 200 with error message
        return {"success": False, "message": "Only Distributor can download this file"}

    # Try to get Distributor doc by user_id (not by name, which is not always user email)
    try:
        distributor_doc = frappe.get_doc("Distributor", {"user_id": user}, ignore_permissions=True)
    except frappe.DoesNotExistError:
        frappe.local.response["message"] = "Distributor record not found"
        frappe.local.response["http_status_code"] = 200  # Return 200 with error message
        return {"success": False, "message": "Distributor record not found"}

    # Check if any company name does NOT contain "endo" (case-insensitive)
    for company in distributor_doc.meril_company_table:
        name = (company.division or "").lower()
        if "endo" not in name:
            # Use the direct file path as requested
            file_docname = frappe.db.get_value("File", {"file_name": "Meril Distributor Compliance policy.pdf"})
            if not file_docname:
                frappe.local.response["message"] = "File not found"
                frappe.local.response["http_status_code"] = 200  # Return 200 with error message
                return {"success": False, "message": "File not found"}

            file_doc = frappe.get_doc("File", file_docname)
            file_path = get_file_path(file_doc.file_url)

            with open(file_path, "rb") as f:
                file_content = f.read()

            # Set response headers for PDF file download
            frappe.response["type"] = "download"
            frappe.response["filename"] = file_doc.file_name
            frappe.response["filecontent"] = file_content
            return

    frappe.local.response["message"] = "Distributor can not access this resource"
    frappe.local.response["http_status_code"] = 200  # Return 200 with error message
    return {"success": False, "message": "Distributor can not access this resource"}

@frappe.whitelist(allow_guest=False)
def downlaod_endo_file():
    user = frappe.session.user

    # Check if user has Distributor role
    user_doc = frappe.get_doc("User", user)
    roles = [role.role for role in user_doc.roles]
    if "Distributor" not in roles:
        frappe.local.response["message"] = "Only Distributor can download this file"
        frappe.local.response["http_status_code"] = 200  # Return 200 with error message
        return {"success": False, "message": "Only Distributor can download this file"}

    # Try to get Distributor doc by user_id (not by name, which is not always user email)
    try:
        distributor_doc = frappe.get_doc("Distributor", {"user_id": user}, ignore_permissions=True)
    except frappe.DoesNotExistError:
        frappe.local.response["message"] = "Distributor record not found"
        frappe.local.response["http_status_code"] = 200  # Return 200 with error message
        return {"success": False, "message": "Distributor record not found"}

    # Check if any company name contains "endo" (case-insensitive)
    for company in distributor_doc.meril_company_table:
        name = (company.division or "").lower()
        if "endo" in name:
            # Use the direct file path as requested
            file_docname = frappe.db.get_value("File", {"file_name": "Meril Distributor Compliance policy for Endo.pdf"})
            if not file_docname:
                frappe.local.response["message"] = "File not found"
                frappe.local.response["http_status_code"] = 200  # Return 200 with error message
                return {"success": False, "message": "File not found"}

            file_doc = frappe.get_doc("File", file_docname)
            file_path = get_file_path(file_doc.file_url)

            with open(file_path, "rb") as f:
                file_content = f.read()

            # Set response headers for file download
            frappe.response["type"] = "download"
            frappe.response["filename"] = file_doc.file_name
            frappe.response["filecontent"] = file_content
            return

    frappe.local.response["message"] = "Distributor can not access this resource"
    frappe.local.response["http_status_code"] = 200  # Return 200 with error message
    return {"success": False, "message": "Distributor can not access this resource"}


@frappe.whitelist(allow_guest=False)
def get_declaration_info():
    user = frappe.session.user
    user_doc = frappe.get_doc("User", user)
    roles = [role.role for role in user_doc.roles]
    if "Distributor" in roles:
        distributor_doc = frappe.get_doc("Distributor", {"user_id": user}, ignore_permissions=True)
        if distributor_doc:
            return distributor_doc
        else:
            return {"success": False, "message": "Distributor record not found"}
    elif "Employee" in roles:
        employee_doc = frappe.get_doc("Employee", {"user_id": user}, ignore_permissions=True)
        if employee_doc:
            return employee_doc
        else:
            return {"success": False, "message": "Employee record not found"}
    else:
        return {"success": False, "message": "User is not a Distributor or Employee"}


@frappe.whitelist(allow_guest=False)
def get_employee_signature(signature, signature_font_type, course):
    user = frappe.session.user

    # Validate user and course
    if not course:
        return {"success": False, "message": "Course is required."}

    # Check course exists
    if not frappe.db.exists("LMS Course", course):
        return {"success": False, "message": "Course does not exist."}

    # Check enrollment and completion
    enrollment = frappe.db.get_value("LMS Enrollment", {"course": course, "member": user}, ["name", "progress"])
    if not enrollment:
        return {"success": False, "message": "User is not enrolled in this course.", "enrollment_required": True}
    enrollment_name, progress = enrollment
    if not progress or int(progress) < 100:
        return {"success": False, "message": "Course progress is not completed.", "progress": progress or 0}

    # Get employee record
    try:
        employee_doc = frappe.get_doc("Employee", {"user_id": user})
    except frappe.DoesNotExistError:
        return {"success": False, "message": "Employee record not found."}

    # Check if Employee Course Documents exists for this employee and course
    employee_course_doc_name = frappe.db.exists(
        "Employee Course Documents",
        {"employee": employee_doc.name, "course": course}
    )

    if not employee_course_doc_name:
        # Create the Employee Course Documents record if not exists
        employee_course_doc = frappe.get_doc({
            "doctype": "Employee Course Documents",
            "employee": employee_doc.name,
            "course": course,
        })
        employee_course_doc.insert(ignore_permissions=True)
        employee_course_doc_name = employee_course_doc.name

    # Check if signature already taken
    employee_course_doc = frappe.get_doc("Employee Course Documents", employee_course_doc_name)
    if employee_course_doc.signature and employee_course_doc.singature_style:
        return {"success": False, "message": "Signature already taken for this course.", "already_signed": True}

    # Save signature, font type, and submission datetime
    employee_course_doc.signature = signature
    employee_course_doc.singature_style = signature_font_type
    employee_course_doc.submission_datetime = now_datetime()
    employee_course_doc.save(ignore_permissions=True)

    return {"success": True, "message": "Signature taken successfully."}


@frappe.whitelist(allow_guest=False)
def get_document_preview_html(course=None, document_type=None, compliance_officer_name=None):
    """
    Get HTML preview of a document using print format templates.
    This returns the HTML content that can be displayed in the frontend for preview.

    Args:
        course: Course name (optional)
        document_type: Type of document to preview (e.g., 'Meril Distributor Compliance Policy Adoption Form')
        compliance_officer_name: Name to use in the document (optional)

    Returns:
        dict: Contains success status and HTML content or error message
    """
    from frappe.utils import now_datetime

    user = frappe.session.user
    user_doc = frappe.get_doc("User", user)
    roles = [role.role for role in user_doc.roles]

    try:
        # Handle Distributor documents
        if "Distributor" in roles:
            distributor_doc = frappe.get_doc("Distributor", {"user_id": user})

            # Validate required fields
            if not distributor_doc.distributor_company_name:
                return {
                    "success": False,
                    "message": "Distributor company name is missing in your profile."
                }

            # Get or create Distributor Course Documents record
            doc = None
            if course:
                doc_name = frappe.db.exists(
                    "Distributor Course Documents",
                    {"distributor": distributor_doc.name, "course": course}
                )
                if doc_name:
                    doc = frappe.get_doc("Distributor Course Documents", doc_name)

            if not doc:
                # Create a temporary document for preview
                doc = frappe.get_doc({
                    "doctype": "Distributor Course Documents",
                    "distributor": distributor_doc.name,
                    "course": course or "",
                    "has_submitted_documents": 0,
                    "entered_name": compliance_officer_name or distributor_doc.attendee_name or "",
                    "submission_datetime": now_datetime()
                })
                # Generate a temporary name without saving
                doc.name = "preview-" + frappe.generate_hash(length=10)
            else:
                # Update with preview values
                if compliance_officer_name:
                    doc.entered_name = compliance_officer_name
                doc.submission_datetime = now_datetime()

            # Determine print format based on document type
            print_format_map = {
                "Meril Distributor Compliance Policy Adoption Form": "Meril Distributor Compliance Policy Adoption Form",
                "Distributor Self Declaration": "Distributor Self Declaration",
                "Meril Distributor Compliance Code of Conduct": "Meril Distributor Compliance Code of Conduct",
                "Distributor Declaration - Ethical Practices & Compliance": "Distributor Declaration - Ethical Practices & Compliance"
            }

            print_format_name = print_format_map.get(document_type)
            if not print_format_name:
                # Default to first available format
                print_format_name = "Meril Distributor Compliance Policy Adoption Form"

            # Generate HTML using the print format
            html_content = frappe.get_print(
                doctype="Distributor Course Documents",
                name=doc.name if doc.name != "preview-" + frappe.generate_hash(length=10) else None,
                doc=doc,  # Pass doc object for preview
                print_format=print_format_name,
                as_pdf=False,  # Get HTML instead of PDF
                no_letterhead=1
            )

            return {
                "success": True,
                "html_content": html_content,
                "document_type": document_type,
                "print_format": print_format_name
            }

        # Handle Employee documents
        elif "Employee" in roles:
            employee_doc = frappe.get_doc("Employee", {"user_id": user})

            # Get or create Employee Course Documents record
            doc = None
            if course:
                doc_name = frappe.db.exists(
                    "Employee Course Documents",
                    {"employee": employee_doc.name, "course": course}
                )
                if doc_name:
                    doc = frappe.get_doc("Employee Course Documents", doc_name)

            if not doc:
                # Create a temporary document for preview
                doc = frappe.get_doc({
                    "doctype": "Employee Course Documents",
                    "employee": employee_doc.name,
                    "course": course or "",
                    "submission_datetime": now_datetime()
                })
                # Generate a temporary name without saving
                doc.name = "preview-" + frappe.generate_hash(length=10)

            # Use Employee Declaration Form print format
            print_format_name = "Employee Declaration Form"

            # Generate HTML using the print format
            html_content = frappe.get_print(
                doctype="Employee Course Documents",
                name=doc.name if doc.name != "preview-" + frappe.generate_hash(length=10) else None,
                doc=doc,  # Pass doc object for preview
                print_format=print_format_name,
                as_pdf=False,  # Get HTML instead of PDF
                no_letterhead=1
            )

            return {
                "success": True,
                "html_content": html_content,
                "document_type": "Employee Declaration Form",
                "print_format": print_format_name
            }

        else:
            return {
                "success": False,
                "message": "User role not supported for document preview"
            }

    except Exception as e:
        frappe.log_error(f"Error generating document preview: {str(e)}")
        return {
            "success": False,
            "message": f"Error generating preview: {str(e)}"
        }

@frappe.whitelist(allow_guest=False)
def get_document_configuration(course=None):
    """
    Get complete document configuration for the current user including:
    - Enabled document types from LMS Settings
    - Division-based document requirements (Endo/Non-Endo)
    - Document categorization (uploadable vs download-only)

    Returns:
        dict: {
            "success": bool,
            "user_role": str,
            "enabled_documents": dict,
            "division_info": dict,
            "document_types": list,
            "uploadable_documents": list,
            "download_only_documents": list
        }
    """
    try:
        user = frappe.session.user
        user_doc = frappe.get_doc("User", user)
        roles = [role.role for role in user_doc.roles]

        # Determine user role
        user_role = None
        if "Distributor" in roles:
            user_role = "Distributor"
        elif "Employee" in roles:
            user_role = "Employee"
        else:
            return {
                "success": False,
                "message": "User role not supported. Must be Distributor or Employee."
            }

        result = {
            "success": True,
            "user_role": user_role,
            "enabled_documents": {},
            "division_info": {},
            "document_types": [],
            "uploadable_documents": [],
            "download_only_documents": []
        }

        if user_role == "Distributor":
            # Get enabled document flags from LMS Settings
            enabled_flags = get_upload_download_docuemtn_enabled()
            if not enabled_flags.get("success"):
                return {
                    "success": False,
                    "message": "Unable to read LMS Settings"
                }

            result["enabled_documents"] = {
                "distributor_self_declaration": enabled_flags.get("distributor_self_declaration", False),
                "meril_distributor_compliance_code_of_conduct": enabled_flags.get("meril_distributor_compliance_code_of_conduct", False),
                "meril_distributor_compliance_policy_adoption_form": enabled_flags.get("meril_distributor_compliance_policy_adoption_form", False),
                "distributor_declaration_ethical_practices": enabled_flags.get("distributor_declaration_ethical_practices", True)  # Default to true if not in settings
            }

            # Get distributor document for division analysis
            distributor_doc = frappe.get_doc("Distributor", {"user_id": user})

            # Analyze divisions
            has_endo = False
            has_non_endo = False
            divisions = []

            for company in distributor_doc.meril_company_table:
                division_name = (company.division or "").lower()
                divisions.append({
                    "company_name": company.meril_company_name,
                    "division": company.division,
                    "is_endo": "endo" in division_name
                })

                if "endo" in division_name:
                    has_endo = True
                else:
                    has_non_endo = True

            result["division_info"] = {
                "has_endo": has_endo,
                "has_non_endo": has_non_endo,
                "divisions": divisions
            }

            # Build document types list based on enabled flags
            document_types = []
            uploadable_documents = []
            download_only_documents = []

            # Add uploadable documents based on enabled flags
            if enabled_flags.get("meril_distributor_compliance_policy_adoption_form"):
                doc = {
                    "key": "meril_distributor_compliance_policy_adoption_form",
                    "name": "Meril Distributor Compliance Policy Adoption Form",
                    "requires_declaration": True,
                    "uploadable": True
                }
                document_types.append(doc)
                uploadable_documents.append(doc)

            if enabled_flags.get("distributor_self_declaration"):
                doc = {
                    "key": "distributor_self_declaration",
                    "name": "Distributor Self Declaration",
                    "requires_declaration": True,
                    "uploadable": True
                }
                document_types.append(doc)
                uploadable_documents.append(doc)

            if enabled_flags.get("meril_distributor_compliance_code_of_conduct"):
                doc = {
                    "key": "meril_distributor_compliance_code_of_conduct",
                    "name": "Meril Distributor Compliance Code of Conduct",
                    "requires_declaration": True,
                    "uploadable": True
                }
                document_types.append(doc)
                uploadable_documents.append(doc)

            # Always add ethical practices declaration if user is distributor
            doc = {
                "key": "distributor_declaration_ethical_practices",
                "name": "Distributor Declaration - Ethical Practices & Compliance",
                "requires_declaration": True,
                "uploadable": True
            }
            document_types.append(doc)
            uploadable_documents.append(doc)

            # Add policy documents based on divisions (download-only)
            if has_endo:
                doc = {
                    "key": "meril_distributor_compliance_policy_endo",
                    "name": "Meril Distributor Compliance Policy for Endo",
                    "requires_declaration": False,
                    "uploadable": False
                }
                document_types.append(doc)
                download_only_documents.append(doc)

            if has_non_endo:
                doc = {
                    "key": "meril_distributor_compliance_policy",
                    "name": "Meril Distributor Compliance Policy",
                    "requires_declaration": False,
                    "uploadable": False
                }
                document_types.append(doc)
                download_only_documents.append(doc)

            result["document_types"] = document_types
            result["uploadable_documents"] = uploadable_documents
            result["download_only_documents"] = download_only_documents

        elif user_role == "Employee":
            # For employees, only show employee declaration form
            doc = {
                "key": "employee_declaration_form",
                "name": "Employee Declaration Form",
                "requires_declaration": True,
                "uploadable": True
            }
            result["document_types"] = [doc]
            result["uploadable_documents"] = [doc]
            result["download_only_documents"] = []
            result["enabled_documents"] = {"employee_declaration_form": True}
            result["division_info"] = {"has_endo": False, "has_non_endo": False, "divisions": []}

        return result

    except Exception as e:
        frappe.log_error(f"Error getting document configuration: {str(e)}")
        return {
            "success": False,
            "message": f"Error getting document configuration: {str(e)}"
        }

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
                return {"success": False, "message": "User Has not Submitted Documents", "role_is": "Distributor" }

            documents_list = [
                "Distributor Completion Certificate",
                "Distributor Self Declaration",
                "Meril Distributor Compliance Code of Conduct"
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
                return {
                    "submited": False,
                    "documents_list": documents_list,
                    "course_documents_record_id": None,
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

import frappe

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

@frappe.whitelist(allow_guest=True)
def generate_dynamic_docx(name=None):
    """
    Generate a PDF directly using Frappe's PDF generation, with the same styling/content
    as the previous docx would have produced, but with increased font size for A4 page.
    """
    import base64
    from frappe.utils import get_datetime

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
        today_long = frappe.utils.format_date(frappe.utils.nowdate(), "d MMMM yyyy")

        # Compose HTML with increased font size for A4 page
        html = f"""
        <html>
        <head>
            <style>
                @page {{
                    size: A4;
                    margin: 40px;
                }}
                body {{
                    font-family: Arial, sans-serif;
                    font-size: 16pt;
                    color: #000;
                    margin: 40px;
                }}
                .center {{
                    text-align: center;
                }}
                .heading {{
                    font-size: 18pt;
                    font-weight: bold;
                    text-decoration: underline;
                    margin-bottom: 18px;
                }}
                .spacer {{
                    height: 60px;
                }}
                .section-title {{
                    font-weight: bold;
                    margin-top: 24px;
                    font-size: 18pt;
                }}
                .info-table {{
                    margin-top: 24px;
                    margin-bottom: 24px;
                    font-size: 16pt;
                }}
                .info-table div {{
                    padding: 4px 12px 4px 0;
                }}
            </style>
        </head>
        <body>
            <div class="center" style="font-size:18pt;">On letter head of distributor</div>
            <div class="spacer"></div>
            <div class="spacer"></div>
            <div class="center heading">Meril Distributor - Compliance Policy Adoption Form</div>
            <div class="spacer"></div>
            <div style="font-size:16pt;">{frappe.utils.format_datetime(frappe.utils.now(), "d MMMM yyyy, h:mm a")} [System Generated]</div>
            <div class="spacer"></div>
            <div style="font-size:16pt;">
                We {distributor_company_name}, being the Distributor of Meril {meril_company_name} do hereby certify that we have willingly adopted attached Meril Distributor Compliance Policy as our own Compliance Policy with effect from {today} and declare to abide by the same.<br><br>
                All employees, partners, directors, proprietor of our organization are expected to observe and adhere to this Policy.
            </div>
            <div class="spacer"></div>
            <div class="section-title">Nomination of Compliance Officer:</div>
            <div class="spacer"></div>
            <div style="font-size:16pt;">
                {name} is nominated as Compliance Officer of our organization with effect from {today_long}
            </div>
            <div class="spacer"></div>
            <div class="section-title">Authorized representative of {distributor_name}</div>
            <div class="info-table">
                <div>Name: {distributor_name}</div>
                <div>Title: {designation}</div>
                <div>Email Id: {email}</div>
                <div>Contact number: {contact_number}</div>
                <div>Sign and Seal :  &lt;Compliance officer nominee name&gt; </div>
            </div>
        </body>
        </html>
        """

        # Generate PDF using Frappe's PDF generator
        pdf_content = frappe.utils.pdf.get_pdf(html)
        pdf_content_base64 = base64.b64encode(pdf_content).decode('utf-8')

        return {
            "success": True,
            "file_content": pdf_content_base64,
            "file_name": "Meril_Distributor_Compliance_Policy_Adoption_Form.pdf"
        }
    except Exception as e:
        frappe.log_error(f"Error generating dynamic pdf: {str(e)}")
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

            # Set response headers for PDF file download
            frappe.response["type"] = "download"
            frappe.response["filename"] = file_doc.file_name
            frappe.response["filecontent"] = file_content
            return

    frappe.local.response["http_status_code"] = 403
    frappe.local.response["message"] = "Distributor can not access this resource"
    return

@frappe.whitelist(allow_guest=False)
def downlaod_endo_file():
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
            frappe.response["type"] = "download"
            frappe.response["filename"] = file_doc.file_name
            frappe.response["filecontent"] = file_content
            return

    frappe.local.response["http_status_code"] = 403
    frappe.local.response["message"] = "Distributor can not access this resource"
    return


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
            frappe.local.response["http_status_code"] = 404
            frappe.local.response["message"] = "Distributor record not found"
            return
    elif "Employee" in roles:
        employee_doc = frappe.get_doc("Employee", {"user_id": user}, ignore_permissions=True)
        if employee_doc:
            return employee_doc
        else:
            frappe.local.response["http_status_code"] = 404
            frappe.local.response["message"] = "Employee record not found"
            return
    else:
        frappe.local.response["http_status_code"] = 403
        frappe.local.response["message"] = "User is not a Distributor or Employee"
        return


@frappe.whitelist(allow_guest=False)
def get_employee_signature(signature, signature_font_type, course):
    user = frappe.session.user

    # Validate user and course
    if not course:
        frappe.local.response["http_status_code"] = 400
        return {"success": False, "message": "Course is required."}

    # Check course exists
    if not frappe.db.exists("LMS Course", course):
        frappe.local.response["http_status_code"] = 404
        return {"success": False, "message": "Course does not exist."}

    # Check enrollment and completion
    enrollment = frappe.db.get_value("LMS Enrollment", {"course": course, "member": user}, ["name", "progress"])
    if not enrollment:
        frappe.local.response["http_status_code"] = 403
        return {"success": False, "message": "User is not enrolled in this course."}
    enrollment_name, progress = enrollment
    if not progress or int(progress) < 100:
        frappe.local.response["http_status_code"] = 403
        return {"success": False, "message": "Course progress is not completed."}

    # Get employee record
    employee_doc = frappe.get_doc("Employee", {"user_id": user})
    if not employee_doc:
        frappe.local.response["http_status_code"] = 404
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
        frappe.local.response["http_status_code"] = 409
        return {"success": False, "message": "Signature already taken for this course."}

    # Save signature, font type, and submission datetime
    employee_course_doc.signature = signature
    employee_course_doc.singature_style = signature_font_type
    employee_course_doc.submission_datetime = now_datetime()
    employee_course_doc.save(ignore_permissions=True)

    return {"success": True, "message": "Signature taken successfully."}

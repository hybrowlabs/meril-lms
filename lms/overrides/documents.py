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
            
@frappe.whitelist(allow_guest=False)
def has_user_submited_document(course=None):
    user = frappe.session.user
    
    if course == None:
        return { "submited": False }

    try:
        # Check if course exists using db.exists instead of get_doc
        if not frappe.db.exists("LMS Course", course):
            return { "submited": False }

        print("course",course)
        exists = frappe.db.exists("User Course Documents", {"user": user, "course": course, "submited_document": 1})
        print("exists",exists)

        user_doc = frappe.get_doc("User", user)
        roles = [role.role for role in user_doc.roles]


        if "Distributor" in roles:
            distributor_doc = frappe.get_doc("Distributor", {"user_id": user})
            documents_list = ["Distributor Self Declaration", "Meril Distributor Compliance Code of Conduct", "Meril Distributor Compliance Policy Adoption Form"]
            
            for company in  distributor_doc.meril_company_table:
                if  company.meril_company_name.lower().find("endo") != -1:
                    documents_list.append("Meril Distributor Compliance Policy for Endo")
                    break

            for company in distributor_doc.meril_company_table:
                if  company.meril_company_name.lower().find("endo") == -1:
                    documents_list.append("Meril Distributor Compliance Policy")
                    break
        elif "Employee" in roles:
            documents_list = ["Employee Self Declaration", "Course Completion Certificate"]
            return { "submited": True, "documents_list": documents_list }
        else:
            documents_list = ["Course Completion Certificate"]
            return { "submited": True, "documents_list": documents_list }

        if  exists:
            return { "submited": True, "documents_list": documents_list }
        
        return { "submited": False, "documents_list": documents_list }
    except Exception as e:
        print(f"Error in has_user_submited_document: {str(e)}")
        frappe.log_error(f"Error in has_user_submited_document: {str(e)}")
        return { "submited": False , "error": str(e)}


@frappe.whitelist(allow_guest=False)
def save_user_course_document_with_file(course=None, document_name=None, filename=None, base64_file_data=None, is_private=1, signature_type=None):
    """
    Save user course document with file upload using base64 data
    """
    user = frappe.session.user
    
    if not course:
        return {"success": False, "message": "No course provided"}
    
    if not document_name:
        return {"success": False, "message": "Document name is required"}
    
    if not filename or not base64_file_data:
        return {"success": False, "message": "File data is required"}
    
    # Debug: Log the first few characters of base64 data
    print(f"Base64 data length: {len(base64_file_data)}")
    print(f"Base64 data preview: {base64_file_data[:50]}...")
    
    try:
        # Validate course exists
        if not frappe.db.exists("LMS Course", course):
            return {"success": False, "message": "Course not found"}
        
        # Check if document already exists for this user and course
        existing_doc = frappe.db.exists("User Course Documents", {"user": user, "course": course})
        
        if existing_doc:
            # Get existing document
            doc = frappe.get_doc("User Course Documents", existing_doc)
            
            # Check if document is already submitted
            if doc.submited_document:
                return {
                    "success": False, 
                    "message": "Document already submitted. You cannot upload another file for this course."
                }
        else:
            # Create new document
            doc = frappe.get_doc({
                "doctype": "User Course Documents",
                "user": user,
                "course": course,
                "submited_document": 0
            })
            doc.insert(ignore_permissions=True)  # Insert the document first to get a name, ignoring permissions
        
        # Decode the base64 file data with proper encoding handling
        try:
            # Clean the base64 string first
            base64_file_data = base64_file_data.strip()
            # Remove any non-base64 characters
            base64_file_data = ''.join(c for c in base64_file_data if c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=')
            
            # Add padding if needed
            padding = 4 - len(base64_file_data) % 4
            if padding != 4:
                base64_file_data += '=' * padding
            
            file_content = base64.b64decode(base64_file_data)
        except Exception as decode_error:
            try:
                # Try URL-safe decoding
                file_content = base64.urlsafe_b64decode(base64_file_data)
            except Exception as url_decode_error:
                try:
                    # Try with different padding
                    base64_file_data = base64_file_data.rstrip('=')
                    padding = 4 - len(base64_file_data) % 4
                    if padding != 4:
                        base64_file_data += '=' * padding
                    file_content = base64.b64decode(base64_file_data)
                except Exception as final_error:
                    frappe.log_error(f"Base64 decode failed: {str(decode_error)}, URL decode failed: {str(url_decode_error)}, Final attempt failed: {str(final_error)}")
                    return {"success": False, "message": "Invalid file data format. Please try uploading the file again."}
        
        # Sanitize filename to handle special characters
        filename = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').decode('ascii')
        print("uploaded file name",filename)
        # Ensure file_content is bytes
        if not isinstance(file_content, bytes):
            file_content = file_content.encode('utf-8') if isinstance(file_content, str) else bytes(file_content)
        
        # Save the file using Frappe's file manager with correct parameters
        file_doc = save_file(
            fname=filename,
            content=file_content,
            dt="User Course Documents",
            dn=doc.name,
            is_private=is_private
        )
        
        # Update document fields
        doc.document_name = document_name
        doc.document_file = file_doc.file_url
        doc.submission_date = now_datetime()
        doc.submited_document = 1
        
        doc.save(ignore_permissions=True)
        
        return {
            "success": True,
            "message": "Document saved successfully",
            "docname": doc.name,
            "file_url": file_doc.file_url,
            "file_name": file_doc.file_name
        }
        
    except Exception as e:
        print("FIle UPlaod error", str(e))
        frappe.log_error(f"Error saving user course document: {str(e)}")
        return {
            "success": False,

            "message": f"Error saving document: {str(e)}"
        }


@frappe.whitelist(allow_guest=False)
def get_user_course_documents(course=None):
    """
    Get user's course documents
    """
    user = frappe.session.user
    
    filters = {"user": user}
    if course:
        filters["course"] = course
    
    documents = frappe.get_all(
        "User Course Documents",
        filters=filters,
        fields=["name", "course", "document_name", "document_file", "submission_date", "submited_document"],
        order_by="creation desc"
    )
    
    return {
        "success": True,
        "documents": documents
    }


@frappe.whitelist(allow_guest=False)
def delete_user_course_document(docname=None):
    """
    Delete user course document
    """
    user = frappe.session.user
    
    if not docname:
        return {"success": False, "message": "No document name provided"}
    
    # Check if document exists and belongs to user
    if not frappe.db.exists("User Course Documents", {"name": docname, "user": user}):
        return {"success": False, "message": "Document not found or access denied"}
    
    try:
        frappe.delete_doc("User Course Documents", docname)
        return {
            "success": True,
            "message": "Document deleted successfully"
        }
    except Exception as e:
        frappe.log_error(f"Error deleting user course document: {str(e)}")
        return {
            "success": False,
            "message": f"Error deleting document: {str(e)}"
        }


@frappe.whitelist(allow_guest=False)
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
        if not distributor_doc.atendee_name:
            frappe.throw("Attendee name is missing in distributor document.")
        if not distributor_doc.designation:
            frappe.throw("Designation is missing in distributor document.")
        if not distributor_doc.distributor_email_address and not user_doc.email:
            frappe.throw("Email address is missing in distributor and user document.")
        if not distributor_doc.distributor_contact_number and not user_doc.mobile_no:
            frappe.throw("Contact number is missing in distributor and user document.")

        meril_company_name = distributor_doc.meril_company_table[0].meril_company_name
        distributor_company_name = distributor_doc.distributor_company_name
        distributor_name = distributor_doc.atendee_name
        designation = distributor_doc.designation
        email = distributor_doc.distributor_email_address or user_doc.email
        contact_number = distributor_doc.distributor_contact_number or user_doc.mobile_no
        today = get_datetime().strftime("%d-%m-%Y")

        doc = Document()
        doc.add_paragraph("On letter head of distributor", style='Normal')
        doc.add_paragraph()
        doc.add_heading("Meril Distributor- Compliance Policy Adoption Form", level=1)
        doc.add_paragraph()
        doc.add_paragraph(today)
        doc.add_paragraph()
        doc.add_paragraph(
            f"We {distributor_company_name}, being the Distributor of Meril {meril_company_name} do hereby certify that we have willingly adopted attached Meril Distributor Compliance Policy as our own Compliance Policy with effect from {today} and declare to abide by the same.\n\n"
            "All employees, partners, directors, proprietor of our organization are expected to observe and adhere to this Policy."
        )
        doc.add_paragraph()
        doc.add_paragraph("Nomination of Compliance Officer:")
        doc.add_paragraph()
        doc.add_paragraph(
            f"{name} is nominated as Compliance Officer of our organization with effect from {today}"
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

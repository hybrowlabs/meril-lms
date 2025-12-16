import frappe
import random
from datetime import timedelta
from frappe.utils import now_datetime, validate_email_address, get_datetime

import requests
from urllib.parse import urlencode
import frappe

@frappe.whitelist(allow_guest=False)
def send_mobile_notification(mobile_no, message):
    """
    Send an SMS notification using the 24x7sms API and log the attempt.
    Args:
        mobile_no (str): The recipient's mobile number.
        message (str): The message to send.
    Returns:
        dict: API response or error message.
    """

    print("send mobile otp function called")
    api_key = frappe.conf.get('sms_api_key')
    service_type = frappe.conf.get('sms_service_type')
    sender_id = frappe.conf.get('sms_sender_id')
    sms_end_point = frappe.conf.get('sms_end_point')

    if not mobile_no or not message:
        return {'response': 'Mobile number and message cannot be empty.'}

    params = {
        'APIKEY': api_key,
        'MobileNo': mobile_no,
        'SenderID': sender_id,
        'Message': message,
        'ServiceName': service_type
    }
    request_url = f"{sms_end_point}?{urlencode(params)}"

    status = 'failure'
    api_response = ''
    try:
        response = requests.get(request_url, timeout=10)
        response.raise_for_status()
        api_response = response.text
        # Check for success in response text (customize as per your API)
        if 'success' in response.text.lower() or response.status_code == 200:
            status = 'success'
        else:
            status = 'failure'
    except requests.exceptions.RequestException as e:
        api_response = f"Something went wrong: {e}"
        status = 'failure'

    # Log the SMS notification
    log_doc = frappe.get_doc({
        'doctype': 'sms_notification_log',
        'mobile_no': mobile_no,
        'message': message,
        'status': status,
        'response': api_response
    })
    log_doc.insert(ignore_permissions=True)

    return {'status': status, 'response': api_response}


def get_user_country_for_otp():
    """Get user's country from User, Employee, or Distributor records."""
    user = frappe.session.user
    country = frappe.db.get_value("User", user, "country")
    
    if not country:
        user_doc = frappe.get_doc("User", user)
        roles = [d.role for d in user_doc.get("roles", [])]
        
        if "Distributor" in roles:
            country = frappe.get_value("Distributor", {"user_id": user}, "country")
        elif "Employee" in roles:
            employee = frappe.get_value("Employee", {"user_id": user}, ["country", "custom_country"], as_dict=True)
            if employee:
                country = employee.get("custom_country") or employee.get("country")
    
    return country


@frappe.whitelist(allow_guest=False)
def requires_mobile_otp():
    """Check if mobile OTP is required based on user's country.
    Returns True for India, False for other countries.
    Defaults to True if country is not set (for safety).
    """
    country = get_user_country_for_otp()
    # India country code/name might be "India" or "IN" depending on system
    is_india = country and (country.upper() == "INDIA" or country.upper() == "IN")
    return {"requires_mobile_otp": is_india if country else True}

        
@frappe.whitelist(allow_guest=False)
def verify_email_otp(otp=None, otp1=None):
    user = frappe.session.user

    user_doc = frappe.get_doc("User", user)

    roles = [d.role for d in user_doc.get("roles", [])]
    email = frappe.db.get_value("User", user, "email")
    mobile = frappe.db.get_value("User", user, "mobile_no")

    if "Distributor" in roles:
        email = frappe.get_value("Distributor", {"user_id": user}, "distributor_email_address")
        mobile = frappe.get_value("Distributor", {"user_id": user}, "distributor_contact_number")
    elif "Employee" in roles:
        email = frappe.get_value("Employee", {"user_id": user}, "company_email") 
        mobile = frappe.get_value("Employee", {"user_id": user}, "cell_number") 

    if not email:
        return {"status": "error", "message": "Missing email"}

    if not otp:
        return {"status": "error", "message": "Email OTP is required"}

    # Check if mobile OTP is required based on country
    country = get_user_country_for_otp()
    is_india = country and (country.upper() == "INDIA" or country.upper() == "IN")
    requires_mobile = is_india if country else True  # Default to True for safety

    # For non-India countries, mobile OTP is optional
    if requires_mobile:
        if not mobile:
            return {"status": "error", "message": "Missing mobile number"}
        if not otp1:
            return {"status": "error", "message": "Mobile OTP is required"}

    filters = {
        "email": email,
        "is_verified": 0,
        "email_otp": otp
    }

    # Only add mobile_otp filter if mobile OTP is required
    if requires_mobile and otp1:
        filters["mobile_otp"] = otp1

    otp_doc = frappe.get_all("Custom Auth Data",
        filters=filters,
        fields=[
            "name",
            "email_otp_expiry_datetime",
            "mobile_otp_expiry_datetime",
            "email_otp",
            "mobile_otp",
            "otp_attempts_remaining",
            "is_expired"
        ],
        order_by="creation desc", limit_page_length=1
    )

    now = now_datetime()

    if not otp_doc:
        # Reduce attempt count if OTP doesn't match
        latest_doc = frappe.get_all("Custom Auth Data",
            filters={"email": email, "is_verified": 0},
            fields=["name", "otp_attempts_remaining", "is_expired"],
            order_by="creation desc", limit_page_length=1
        )
        if latest_doc:
            doc = frappe.get_doc("Custom Auth Data", latest_doc[0].name)
            if not doc.is_expired:
                doc.otp_attempts_remaining -= 1
                if doc.otp_attempts_remaining <= 0:
                    doc.is_expired = 1
                doc.save(ignore_permissions=True)
        return {"status": "error", "message": "Invalid OTP"}

    otp_doc = otp_doc[0]

    email_expired = otp_doc.email_otp and now > get_datetime(otp_doc.email_otp_expiry_datetime)
    mobile_expired = otp_doc.mobile_otp and now > get_datetime(otp_doc.mobile_otp_expiry_datetime)

    # Email OTP is always required
    email_valid = otp and otp == otp_doc.email_otp and not email_expired
    
    # Mobile OTP is only required for India
    mobile_valid = True  # Default to True for non-India countries
    if requires_mobile:
        mobile_valid = otp1 and otp1 == otp_doc.mobile_otp and not mobile_expired
    
    valid = email_valid and mobile_valid

    doc = frappe.get_doc("Custom Auth Data", otp_doc.name)

    if valid and not doc.is_expired:
        doc.is_verified = 1
        doc.unlocked_at = now
        doc.locked_at = now + timedelta(minutes=60)
        doc.user = user
        doc.save(ignore_permissions=True)
        return {"status": "success", "message": "OTP verified and user unlocked"}

    else:
        if not doc.is_expired:
            doc.otp_attempts_remaining -= 1
            if doc.otp_attempts_remaining <= 0:
                doc.is_expired = 1
            doc.save(ignore_permissions=True)

        return {"status": "error", "message": "OTP expired or invalid"}


@frappe.whitelist(allow_guest=False)
def send_email_otp():
    try:
        user = frappe.session.user
        user_doc = frappe.get_doc("User", user)

        roles = [d.role for d in user_doc.get("roles", [])]
        email = frappe.db.get_value("User", user, "email")
        mobile = frappe.db.get_value("User", user, "mobile_no")

        if "Distributor" in roles:
            email = frappe.get_value("Distributor", {"user_id": user}, "distributor_email_address") 
            mobile = frappe.get_value("Distributor", {"user_id": user}, "distributor_contact_number") 
            print("distritbutor", email, mobile)
        elif "Employee" in roles:
            email = frappe.get_value("Employee", {"user_id": user}, "company_email") 
            mobile = frappe.get_value("Employee", {"user_id": user}, "cell_number") 
            print("employee", email, mobile)
        print(email, mobile)
        if not email:
            return {"status": "error", "message": "User email not found"}

        # Check if mobile OTP is required based on country
        country = get_user_country_for_otp()
        is_india = country and (country.upper() == "INDIA" or country.upper() == "IN")
        requires_mobile = is_india if country else True  # Default to True for safety

        # For non-India countries, mobile is optional
        if requires_mobile and not mobile:
            return {"status": "error", "message": "User mobile not found"}

        now = now_datetime()

        latest_doc = frappe.get_all("Custom Auth Data", filters={
            "email": email,
            "is_verified": 0,
            "is_expired": 0
        }, fields=[
            "name", "email_otp", "mobile_otp",
            "email_otp_expiry_datetime", "mobile_otp_expiry_datetime"
        ], order_by="creation desc", limit=1)

        email_otp = str(random.randint(100000, 999999))
        mobile_otp = str(random.randint(100000, 999999))

        # Always initialize these before use
        email_sent = False
        mobile_sent = False
        email_error = None
        mobile_error = None

        if latest_doc:
            otp_info = latest_doc[0]
            email_expired = otp_info.email_otp_expiry_datetime and now > otp_info.email_otp_expiry_datetime
            mobile_expired = otp_info.mobile_otp_expiry_datetime and now > otp_info.mobile_otp_expiry_datetime

            # Resend if email is expired (always required)
            # For India users, also resend if mobile is expired
            if email_expired or (requires_mobile and mobile_expired):
                try:
                    frappe.db.set_value("Custom Auth Data", otp_info.name, "is_expired", 1)
                    frappe.db.commit()
                    

                    new_doc = frappe.get_doc({
                        "doctype": "Custom Auth Data",
                        "email": email,
                        "email_otp": email_otp,
                        "mobile_otp": mobile_otp,
                        "email_otp_expiry_datetime": now + timedelta(minutes=15),
                        "mobile_otp_expiry_datetime": now + timedelta(minutes=15),
                        "otp_attempts_remaining": 3,
                        "is_verified": 0,
                        "is_expired": 0,
                        "user": user
                    })
                    new_doc.insert(ignore_permissions=True)

                    # Try sending email OTP
                    try:
                        frappe.sendmail(
                            recipients=[email],
                            subject="Your Email OTP Code (Resent)",
                            message=f"Your Email OTP is <b>{email_otp}</b>. It will expire in 15 minutes.",
                            now=True
                        )
                        email_sent = True
                    except Exception as e:
                        email_error = str(e)
                        frappe.log_error(frappe.get_traceback(), "Error sending email OTP (resent)")

                    # Try sending mobile OTP via SMS only for India
                    if requires_mobile and mobile:
                        try:
                            sms_result = send_mobile_notification(
                                mobile_no=mobile,
                                message=f"Dear User, Your OTP to login in Meril App is {mobile_otp}. Valid only for 15 minutes."
                            )
                            mobile_sent = bool(sms_result and sms_result.get('status') == 'success')
                            if not mobile_sent:
                                mobile_error = (sms_result or {}).get('response') or 'SMS gateway reported failure'
                        except Exception as e:
                            mobile_error = str(e)
                            frappe.log_error(frappe.get_traceback(), "Error sending mobile OTP (resent)")
                    else:
                        # For non-India countries, mobile OTP is not sent via SMS
                        mobile_sent = True  # Consider it successful since it's not required

                    if email_sent:
                        if requires_mobile:
                            if mobile_sent:
                                return {"status": "resent", "message": "Previous OTPs resent in a new record"}
                            else:
                                return {"status": "resent", "message": "Email OTP sent, but failed to send mobile OTP", "mobile_error": mobile_error}
                        else:
                            return {"status": "resent", "message": "Email OTP resent in a new record"}
                    else:
                        return {"status": "error", "message": "Failed to send email OTP", "email_error": email_error}
                except Exception as e:
                    frappe.log_error(frappe.get_traceback(), "Error resending OTPs")
                    return {"status": "error", "message": f"Failed to resend OTPs: {str(e)}"}

        try:
            new_doc = frappe.get_doc({
                "doctype": "Custom Auth Data",
                "email": email,
                "email_otp": email_otp,
                "mobile_otp": mobile_otp,
                "email_otp_expiry_datetime": now + timedelta(minutes=15),
                "mobile_otp_expiry_datetime": now + timedelta(minutes=15),
                "otp_attempts_remaining": 3,
                "is_verified": 0,
                "is_expired": 0,
                "user": user
            })

            new_doc.insert(ignore_permissions=True)

            # Reset context for new send
            email_sent = False
            mobile_sent = False
            email_error = None
            mobile_error = None

            try:
                frappe.sendmail(
                    recipients=[email],
                    subject="Your Email OTP Code",
                    message=f"Your Email OTP is <b>{email_otp}</b>. It will expire in 15 minutes.",
                    now=True
                )
                email_sent = True
            except Exception as e:
                email_error = str(e)
                frappe.log_error(frappe.get_traceback(), "Error sending email OTP (new)")

            # Try sending mobile OTP via SMS only for India
            if requires_mobile and mobile:
                try:
                    sms_result = send_mobile_notification(
                        mobile_no=mobile,
                        message=f"Dear User, Your OTP to login in Meril App is {mobile_otp}. Valid only for 15 minutes."
                    )
                    mobile_sent = bool(sms_result and sms_result.get('status') == 'success')
                    if not mobile_sent:
                        mobile_error = (sms_result or {}).get('response') or 'SMS gateway reported failure'
                except Exception as e:
                    mobile_error = str(e)
                    frappe.log_error(frappe.get_traceback(), "Error sending mobile OTP (new)")
            else:
                # For non-India countries, mobile OTP is not sent via SMS
                mobile_sent = True  # Consider it successful since it's not required

            if email_sent:
                if requires_mobile:
                    if mobile_sent:
                        return {"status": "new", "message": "New OTPs sent"}
                    else:
                        return {"status": "new", "message": "Email OTP sent, but failed to send mobile OTP", "mobile_error": mobile_error}
                else:
                    return {"status": "new", "message": "Email OTP sent"}
            else:
                return {"status": "error", "message": "Failed to send email OTP", "email_error": email_error}
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Error sending new OTPs")
            return {"status": "error", "message": f"Failed to send OTPs: {str(e)}"}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in send_email_otp")
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}

# @frappe.whitelist(allow_guest=False)
# def send_mobile_otp():
#     user = frappe.session.user
#     if user == "Guest":
#         return {"status": "error", "message": "Please log in to send OTP"}

#     mobile = frappe.db.get_value("User", user, "mobile_no")
#     email = frappe.db.get_value("User", user, "email")

#     if not mobile:
#         return {"status": "error", "message": "User mobile not found"}
    
#     if not email:
#         return {"status": "error", "message": "User email not found"}

#     now = now_datetime()

#     latest_doc = frappe.get_all("Custom Auth Data", filters={
#         "user": user,
#         "mobile": mobile,
#         "is_verified": 0,
#         "is_expired": 0
#     }, fields=[
#         "name", "mobile_otp", "mobile_otp_expiry_datetime", "email_otp"
#     ], order_by="creation desc", limit=1)

#     mobile_otp = str(random.randint(100000, 999999))
#     email_otp = latest_doc[0].email_otp

#     if latest_doc:
#         otp_info = latest_doc[0]
#         mobile_expired = otp_info.mobile_otp_expiry_datetime and now > otp_info.mobile_otp_expiry_datetime

#         if mobile_expired:
#             old_doc = frappe.get_doc("Custom Auth Data", otp_info.name)
#             old_doc.is_expired = 1
#             old_doc.save(ignore_permissions=True)

#             new_doc = frappe.get_doc({  
#                 "doctype": "Custom Auth Data",
#                 "mobile": mobile,
#                 "mobile_otp": mobile_otp,
#                 "mobile_otp_expiry_datetime": now + timedelta(minutes=15),
#                 "email": email,
#                 "email_otp": email_otp, 
#                 "email_otp_expiry_datetime": now + timedelta(minutes=15),
#                 "otp_attempts_remaining": 3,
#                 "is_verified": 0,
#                 "is_expired": 0,
#                 "user": user
#             })
#             new_doc.insert(ignore_permissions=True)

#             #send mobile otp to email for now
#             frappe.sendmail(
#                 recipients=[email],
#                 subject="Your Mobile OTP Code",
#                 message=f"Your Mobile OTP is <b>{mobile_otp}</b>. It will expire in 15 minutes.",
#                 now=True
#             )

#             return {"status": "new", "message": "New Mobile OTP sent"}
#         else 
#             frappe.sendmail(
#                 recipients=[email],
#                 subject="Your Mobile OTP Code",
#                 message=f"Your Mobile OTP is <b>{latest_doc[0].mobile_otp}</b>. It will expire in 15 minutes.",
#                 now=True
#             )
#             return {"status": "resend", "message": "Resend Mobile OTP"}
#     else:
#         return {"status": "error", "message": "No verification data found"}


# @frappe.whitelist(allow_guest=False)
# def send_otp_to_email():
#     user = frappe.session.user
#     if user == "Guest":
#         return {"status": "error", "message": "Please log in to send OTP"}

#     mobile = frappe.db.get_value("User", user, "mobile_no")
#     email = frappe.db.get_value("User", user, "email")

#     if not mobile:
#         return {"status": "error", "message": "User mobile not found"}
    
#     if not email:
#         return {"status": "error", "message": "User email not found"}

#     now = now_datetime()

#     latest_doc = frappe.get_all("Custom Auth Data", filters={
#         "user": user,
#         "mobile": mobile,
#         "is_verified": 0,
#         "is_expired": 0
#     }, fields=[
#         "name", "mobile_otp", "mobile_otp_expiry_datetime", "email_otp", "email_otp_expiry_datetime"
#     ], order_by="creation desc", limit=1)

#     mobile_otp = latest_doc[0].mobile_otp
#     email_otp = str(random.randint(100000, 999999))

#     if latest_doc:
#         otp_info = latest_doc[0]
#         email_expired = otp_info.email_otp_expiry_datetime and now > otp_info.email_otp_expiry_datetime

#         if email_expired:
#             old_doc = frappe.get_doc("Custom Auth Data", otp_info.name)
#             old_doc.is_expired = 1
#             old_doc.save(ignore_permissions=True)

#             new_doc = frappe.get_doc({  
#                     "doctype": "Custom Auth Data",
#                     "mobile": mobile,
#                     "mobile_otp": mobile_otp,
#                     "mobile_otp_expiry_datetime": now + timedelta(minutes=15),
#                     "email": email,
#                     "email_otp": email_otp, 
#                     "email_otp_expiry_datetime": now + timedelta(minutes=15),
#                     "otp_attempts_remaining": 3,
#                     "is_verified": 0,
#                     "is_expired": 0,
#                 "user": user
#             })
#             new_doc.insert(ignore_permissions=True)

#             #send mobile otp to email for now
#             frappe.sendmail(
#                 recipients=[email],
#                 subject="Your Email OTP Code",
#                 message=f"Your Email OTP is <b>{email_otp}</b>. It will expire in 15 minutes.",
#                 now=True
#             )

#             return {"status": "new", "message": "New Email OTP sent"}
#         else 
#             frappe.sendmail(
#                 recipients=[email],
#                 subject="Your Email OTP Code",
#                 message=f"Your Email OTP is <b>{latest_doc[0].email_otp}</b>. It will expire in 15 minutes.",
#                 now=True
#             )
#             return {"status": "resend", "message": "Resend Email OTP"}
#     else:
#         return {"status": "error", "message": "No verification data found"}


@frappe.whitelist(allow_guest=False)
def get_user_status():
    user = frappe.session.user

    user_doc = frappe.get_doc("User", user)
    roles = [role.role for role in user_doc.roles]

    if "System Manager" in roles or "Administrator" in roles or "Supervisor" in roles:
        return {"status": "unlocked", "message": "User is unlocked."}

    # Check if user is excluded from OTP verification
    try:
        lms_settings = frappe.get_single("LMS Settings")
        excluded_users = lms_settings.get("otp_excluded_users", [])
        for excluded_user in excluded_users:
            if excluded_user.user == user and excluded_user.disabled == 1:
                return {"status": "unlocked", "message": "User is excluded from OTP verification"}
    except Exception as e:
        # If there's an error checking excluded users, log it but continue with normal flow
        frappe.log_error(frappe.get_traceback(), "Error checking OTP excluded users")

    email = frappe.db.get_value("User", user, "email")
    if not email:
        return {"status": "error", "message": "Email not found"}

    try:
        auth_data = frappe.get_all("Custom Auth Data",
            filters={"email": email, "is_verified": 1},
            fields=["name", "locked_at", "unlocked_at"],
            order_by="creation desc", limit=1
        )

        if not auth_data:
            return {"status": "error", "message": "No verification data found"}

        auth = auth_data[0]
        now = now_datetime()

        if auth.get("locked_at") and now > auth.get("locked_at"):
            return {"status": "locked", "message": "Session expired. Please verify OTP again."}

        return {"status": "unlocked", "message": "User is unlocked."}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_user_status error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist(allow_guest=False)
def should_user_redirect():
    user = frappe.session.user
    user_doc = frappe.get_doc("User", {"name": user}, ["roles"])
    can_edit_own_profile = "Can Edit Own Profile" in [role.role for role in user_doc.roles]
    is_distributor = frappe.db.exists("Distributor", {"user_id": user})

    if can_edit_own_profile and is_distributor:
        return {"status": "redirect", "message": "User is a distributor. Redirecting to distributor profile."}
    else:
        return {"status": "no_redirect", "message": "User is not a distributor."}

documents_list = ["Distributor Self Declaration", "Meril Distributor Compliance Code of Conduct", "Meril Distributor Compliance Policy Adoption Form"]
import frappe
from frappe import _
from frappe.model.naming import append_number_if_name_exists
from frappe.website.utils import cleanup_page_name
from frappe.website.utils import is_signup_disabled
from frappe.utils import random_string, escape_html
from lms.lms.utils import get_country_code
import random
import string
import frappe
from frappe.utils.password import update_password
import json

def validate_username_duplicates(doc, method):
	while not doc.username or doc.username_exists():
		doc.username = append_number_if_name_exists(
			doc.doctype, cleanup_page_name(doc.full_name), fieldname="username"
		)
	if " " in doc.username:
		doc.username = doc.username.replace(" ", "")

	if len(doc.username) < 4:
		doc.username = doc.email.replace("@", "").replace(".", "")


def after_insert(doc, method):
	doc.add_roles("LMS Student")

## FUNCTIONS FOR CUSTOM SIGNUP FLOW

def generate_and_save_otp():
	otp = "123456"
	return otp

def create_user_from_employee(self, method=None):
	full_name = self.first_name + " " + self.last_name if self.last_name else self.first_name
	email = self.company_email 
	country = self.custom_country 

	print( "email", email, "country", country)
	# Check if user already exists
	try:
		if not frappe.db.exists("User", email):
			new_password = frappe.generate_hash(length=10)

			if not self.user_id:
				# if user is not created, then create user
				self.user_id = frappe.get_doc(
					{
						"doctype": "User",
						"email": self.company_email,
						"first_name": self.first_name,
						"full_name": full_name,
						"enabled": 1,
						"user_type": "Website User",						
						"new_password": new_password,
						"user_category": "Employee",
						"mobile_no": self.employee_number,
						"send_welcome_email": 0,
					}
					).insert(ignore_permissions=True).email

				self.db_set("user_id", self.user_id)
				update_password(email, new_password)
				
				# Update self in the database
				frappe.sendmail(
					recipients=[self.company_email],	
					sender='noreply@merilms.com',
					subject='Test Email',	
					message=f'<p>Hello {self.first_name} from meril lms for your email {self.company_email} your password is : {new_password} </p>'
				)

				# self.db_set("user_id", self.user_id)
		else:
				frappe.throw(_("A user with this email already exists."))
		
		print("User created successfully")
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Employee Creation Process Failed")
		frappe.throw(_("An error occurred during employee creation: {0}").format(str(e)))


def generate_password(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def create_user_from_distributor(self, method=None):
    email = self.distributor_email_address
    country = self.country

    print("email", email, "country", country)

    try:
        if not frappe.db.exists("User", email):
            new_password = generate_password()

            if not self.user_id:
                # Create the user
                user = frappe.get_doc({
                    "doctype": "User",
                    "email": email,
                    "enabled": 1,
                    "user_type": "Website User",
                    "send_welcome_email": 0,
					"mobile_no": self.distributor_contact_number,
					"first_name": email.split('@')[0],  # Use email prefix as first name
                    "user_category": "Distributor",
			"roles": [
				{"role": "Distributor"},
				{"role": "LMS Student"},
				{"role": "Can Edit Own Profile"}
			],
			"country": country
		}).insert(ignore_permissions=True)

                update_password(email, new_password)
                print("user", user)
                self.db_set("user_id", user.name)

                frappe.sendmail(
                    recipients=[email],
                    sender='noreply@merlinlms.com',
                    subject='Your Merlin LMS Account',
                    message=f'<p>Hello {email},<br>Your password is: <b>{new_password}</b><br>Regards,<br>Merlin LMS</p>'
                )
        else:
            frappe.throw(_("A user with this email already exists."))

        print("User created successfully")

    except Exception as e:
        print("ERROR:", str(e))
        frappe.log_error(frappe.get_traceback(), "Distributor Creation Process Failed")
        frappe.throw(_("An error occurred during distributor creation: {0}").format(str(e)))



@frappe.whitelist(allow_guest=True)
def sign_up(email, full_name, verify_terms, user_category):
	if is_signup_disabled():
		frappe.throw(_("Sign Up is disabled"), _("Not Allowed"))

	user = frappe.db.get("User", {"email": email})
	if user:
		if user.enabled:
			return 0, _("Already Registered")
		else:
			return 0, _("Registered but disabled")
	else:
		if frappe.db.get_creation_count("User", 60) > 300:
			frappe.respond_as_web_page(
				_("Temporarily Disabled"),
				_(
					"Too many users signed up recently, so the registration is disabled. Please try back in an hour"
				),
				http_status_code=429,
			)

	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": escape_html(full_name),
			"verify_terms": verify_terms,
			"user_category": user_category,
			"country": "",
			"enabled": 1,
			"new_password": random_string(10),
			"user_type": "Website User",
		}
	)
	user.flags.ignore_permissions = True
	user.flags.ignore_password_policy = True
	user.insert()

	# set default signup role as per Portal Settings
	default_role = frappe.db.get_single_value("Portal Settings", "default_role")
	if default_role:
		user.add_roles(default_role)

	user.add_roles("LMS Student")
	set_country_from_ip(None, user.name)

	if user.flags.email_sent:
		return 1, _("Please check your email for verification")
	else:
		return 2, _("Please ask your administrator to verify your sign-up")


def set_country_from_ip(login_manager=None, user=None):
	if not user and login_manager:
		user = login_manager.user
	user_country = frappe.db.get_value("User", user, "country")
	# if user_country:
	#    return
	frappe.db.set_value("User", user, "country", get_country_code())
	return


def on_login(login_manager):
	user_id = login_manager.user

	default_app = frappe.db.get_single_value("System Settings", "default_app")
	if default_app == "lms":
		frappe.local.response["home_page"] = "/lms"

@frappe.whitelist(allow_guest=False)
def get_distributor_profile(user_id=None):
	user_name = frappe.session.user
	user_doc = frappe.get_doc("User", {"name": frappe.session.user})
	roles = [role.role for role in user_doc.roles]
	can_edit_own_profile = "Can Edit Own Profile" in roles
	
	fields = [ 
		"name",
		"division",
		"meril_company_name",
		"bu__fd_head",
		"rsm__state_head",
		"region",
		"state",
		"city",
		"account__distributor_code",
		"distributor_email_address",
		"distributor_company_address",
		"distributor_contact_number",
		"atendee_name",
		"designation"
	]
	distributor = frappe.db.get_value("Distributor", {"user_id": user_name }, fields, as_dict=True)
	
	# Get the child table data separately
	if distributor:
		meril_company_table = frappe.get_all(
			"Meril Distributor Division Child",
			filters={"parent": distributor.name},
			fields=["division", "meril_company_name"]
		)
		
		distributor["meril_company_table"] = meril_company_table
		
	
	if distributor and not can_edit_own_profile:
		frappe.local.response["home_page"] = "/lms"
		return None
	else:
		frappe.local.response["home_page"] = "/edit-distributor-profile"
	return distributor

@frappe.whitelist(allow_guest=False)
def update_distributor_profile(data):
    data = json.loads(data)
    user_id = frappe.session.user
    user_doc = frappe.get_doc("User", user_id)
    roles = [role.role for role in user_doc.roles]
    can_edit_own_profile = "Can Edit Own Profile" in roles

    distributor = frappe.get_doc("Distributor", {"user_id": user_id})
    if "Distributor" in roles and not can_edit_own_profile :
        frappe.local.response["redirect"] = "/lms"
        return
    elif distributor and not can_edit_own_profile: 
        frappe.local.response["redirect"] = "/lms"
        return
    else:
        filter_data = [
            "division", "meril_company_name", "bu__fd_head", "rsm__state_head", "region",
            "state", "city", "account__distributor_code", "distributor_company_name",
            "distributor_email_address", "distributor_company_address", "distributor_contact_number", "atendee_name", "designation"
        ]
        filtered_data = {}
        print("data", data)
        for key, value in data.items():
            if key in filter_data:
                filtered_data[key] = value
        distributor.update(filtered_data)
        
        # Handle child table data if provided
        if "meril_company_table" in data and data["meril_company_table"]:
            # Clear existing child table entries
            distributor.meril_company_table = []
            
            # Add new child table entries
            for item in data["meril_company_table"]:
                distributor.append("meril_company_table", {
                    "division": item.get("division"),
                    "meril_company_name": item.get("meril_company_name")
                })
        
        distributor.save(ignore_permissions=True)
        user_doc.roles = [role for role in user_doc.roles if role.role != "Can Edit Own Profile"]
        user_doc.save(ignore_permissions=True)
        frappe.local.response["redirect"] = "/lms"
    return distributor





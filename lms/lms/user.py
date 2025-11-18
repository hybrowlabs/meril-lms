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

def get_default_sender():
	"""Get the default outgoing email account"""
	try:
		default_email_account = frappe.get_doc("Email Account", {"default_outgoing": 1})
		return default_email_account.email_id
	except:
		# Fallback to system default if no default outgoing email account is found
		return frappe.db.get_single_value("System Settings", "auto_email_id") or "noreply@example.com"

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

@frappe.whitelist()
def create_user_from_employee(employee_id, _method):
	# Check if automatic user creation is enabled when called as hook
	if _method == "after_insert":  # Called as hook from Employee creation
		lms_settings = frappe.get_single("LMS Settings")
		if not getattr(lms_settings, "auto_create_employee_users", False):
			frappe.logger().info(f"Automatic user creation is disabled for employee: {employee_id}")
			return

	frappe.only_for(["Supervisor", "System User"])

	employee_doc = frappe.get_doc("Employee", employee_id)
	full_name = employee_doc.first_name + " " + employee_doc.last_name if employee_doc.last_name else employee_doc.first_name
	email = employee_doc.company_email 
	country = employee_doc.custom_country 

	print( "email", email, "country", country)
	# Check if user already exists
	try:
		if not frappe.db.exists("User", email):
			new_password = frappe.generate_hash(length=10)

			if not employee_doc.user_id:
				# if user is not created, then create user
				employee_doc.user_id = frappe.get_doc(
					{
						"doctype": "User",
						"email": employee_doc.company_email,
						"first_name": employee_doc.first_name,
						"full_name": full_name,
						"enabled": 1,
						"user_type": "Website User",						
						"new_password": new_password,
						"user_category": "Employee",
						"mobile_no": employee_doc.cell_number,
						"send_welcome_email": 0,
					}
					).insert(ignore_permissions=True).email

				employee_doc.db_set("user_id", employee_doc.user_id)
				update_password(email, new_password)

				user_doc = frappe.get_doc("User", email)
				reset_password_link = user_doc.reset_password(send_email=False)
				login_url = frappe.utils.get_url("/login")
				recipient_name = (
					employee_doc.employee_name or employee_doc.first_name or full_name
				)

				subject = "Ethics & Compliance Training on HCPs/HCOs Interactions."
				message = f"""<p>Dear {recipient_name},</p>

<p>In line with our mandatory training, you have been enrolled for the <span style="font-weight:bold;">Ethics & Compliance Training on HCPs/HCOs Interactions.</span> This training is essential to ensure adherence to our ethical standards and regulatory guidelines.</p>

<p style="font-weight:bold;">Login Credentials:</p>
<p>Please click on the below link to log in:</p>
<p>(<a href="{login_url}">{login_url}</a>)</p>
<p>User ID: {email}</p>
<p>Password: (<a href="{reset_password_link}">Reset password</a>)</p>

<p>We kindly request you to complete this training at your earliest. Timely completion is important to maintain compliance and avoid any lapses in regulatory obligations.</p>

<p>Best regards,</p>
<p>Meril</p>"""

				frappe.sendmail(
					recipients=[employee_doc.company_email],
					sender=get_default_sender(),
					subject=subject,
					message=message,
				)
				# Create a Notification Log to send system notification
				frappe.get_doc({
					"doctype": "Notification Log",
					"subject": subject,
					"email_content": message,
					"for_user": employee_doc.company_email,
					"type": "Alert",
					"document_type": "Employee",
					"document_name": employee_doc.name
				}).insert(ignore_permissions=True)

				# self.db_set("user_id", self.user_id)
		else:
			frappe.throw(_("A user with this email already exists."))
		print("User created successfully")
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Employee Creation Process Failed")
		frappe.throw(_("An error occurred during employee creation: {0}").format(str(e)))


def generate_password(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def get_distributor_initial_email_template(distributor_doc, email, reset_password_link):
	"""Generate the initial email template for distributor user creation/resend"""
	subject = f'Ethics & Compliance Training on HCP/HCO Interactions'
	message = f'''<p>Dear {distributor_doc.distributor_name},</p>

		<p>In line with our <span style="font-weight: bold;"> mandatory training,</span> you have been enrolled for the <span style="font-weight: bold;">Ethics & Compliance Training on HCP/HCO Interactions</span> This training is essential to ensure adherence to our ethical standards and regulatory guidelines.</p>

		<p style="font-weight: bold;">Login Credentials:</p>
		<p style="font-weight: bold;margin-left:10px;"><span style="margin-right: 10px;">•</span>  Please click on the below link to log in:</p>
		<a href="{frappe.utils.get_url("/login")}">{frappe.utils.get_url("/login")}</a>
		<p style="margin-left:10px; margin-bottom: 0;font-weight: bold;"><span style="margin-right: 10px;">•</span> User ID: <span style="font-weight:normal;">{email}</span></p>
		<p style="margin-left:10px; margin-top: 0;font-weight: bold;"><span style="margin-right: 10px;">•</span> Reset Password Link: <a href="{reset_password_link}">Click here to reset your password</a></p>


		<p>We kindly request you to complete this training at the earliest and ensure that your employees are also trained. Please maintain proper records of the training completed by you and your employees for compliance purposes.</p>

		<p>Best regards,</p>
		<p>Meril</p>
		'''
	return subject, message


@frappe.whitelist()
def get_distributors_by_division(division, filters=None):
	"""
	Get distributors filtered by division from child table
	"""
	if filters is None:
		filters = {}

	# Parse filters if it's a string (JSON)
	if isinstance(filters, str):
		filters = frappe.parse_json(filters)

	# Remove division from filters since we'll handle it separately
	filters.pop('division', None)

	# Build the SQL query to join with child table
	conditions = ["d.name = c.parent"]

	if division:
		conditions.append("c.division = %(division)s")

	# Add other filters
	for field, value in filters.items():
		if field == 'user_id' and isinstance(value, list) and value[0] == 'is' and value[1] == 'not set':
			conditions.append("(d.user_id IS NULL OR d.user_id = '')")
		elif isinstance(value, list):
			# Handle list conditions like ['like', '%value%']
			operator = value[0]
			filter_value = value[1]
			conditions.append(f"d.{field} {operator} %({field}_value)s")
			filters[f"{field}_value"] = filter_value
		else:
			conditions.append(f"d.{field} = %({field})s")

	query = f"""
		SELECT DISTINCT
			d.name,
			d.attendee_name,
			d.distributor_name,
			d.distributor_email_address,
			d.distributor_company_name,
			d.country,
			d.state,
			d.city,
			d.user_id,
			d.is_active_user
		FROM `tabDistributor` d
		LEFT JOIN `tabMeril Distributor Division Child` c ON d.name = c.parent
		WHERE {' AND '.join(conditions)}
		ORDER BY d.creation DESC
		LIMIT 100
	"""

	filters['division'] = division

	result = frappe.db.sql(query, filters, as_dict=True)
	return result

@frappe.whitelist()
def bulk_create_users_from_distributors(distributor_ids, filters=None):
	"""
	Create users for multiple distributors and send emails
	distributor_ids: List of distributor IDs to create users for
	filters: Optional filters used to select these distributors (for logging)
	"""
	frappe.only_for(["Administrator", "Supervisor", "System User"])

	if isinstance(distributor_ids, str):
		distributor_ids = frappe.parse_json(distributor_ids)

	if isinstance(filters, str):
		filters = frappe.parse_json(filters)

	results = {
		"success": [],
		"errors": [],
		"already_exists": [],
		"total": len(distributor_ids)
	}

	for distributor_id in distributor_ids:
		try:
			distributor_doc = frappe.get_doc("Distributor", distributor_id)
			email = distributor_doc.distributor_email_address

			# Check if user already exists
			if frappe.db.exists("User", email):
				results["already_exists"].append({
					"distributor_id": distributor_id,
					"name": distributor_doc.attendee_name or distributor_doc.distributor_name,
					"email": email,
					"message": "User already exists"
				})
				continue

			# Check if distributor already has a user_id
			if distributor_doc.user_id:
				results["already_exists"].append({
					"distributor_id": distributor_id,
					"name": distributor_doc.attendee_name or distributor_doc.distributor_name,
					"email": email,
					"message": "User already linked to distributor"
				})
				continue

			# Create the user using the existing single function
			create_user_from_distributor(distributor_id)

			results["success"].append({
				"distributor_id": distributor_id,
				"name": distributor_doc.attendee_name or distributor_doc.distributor_name,
				"email": email,
				"message": "User created and email sent successfully"
			})

		except Exception as e:
			results["errors"].append({
				"distributor_id": distributor_id,
				"name": getattr(frappe.get_doc("Distributor", distributor_id), 'attendee_name', distributor_id),
				"error": str(e)
			})
			frappe.log_error(f"Failed to create user for distributor {distributor_id}: {str(e)}", "Bulk User Creation Error")

	# Send summary email to admins
	if results["success"] or results["errors"]:
		send_bulk_creation_summary_email(results, filters)

	return results

@frappe.whitelist()
def resend_initial_email_to_distributor(distributor_id):
	"""
	Resend the initial email to a distributor who already has a user account.
	This regenerates the password reset link and sends the same email as initial creation.
	"""
	frappe.only_for(["Administrator", "Supervisor", "System User"])

	distributor_doc = frappe.get_doc("Distributor", distributor_id)
	email = distributor_doc.distributor_email_address

	if not distributor_doc.user_id:
		frappe.throw(_("Distributor does not have a user account. Use 'Create Users & Send Emails' instead."))

	try:
		# Get the user document
		if not frappe.db.exists("User", distributor_doc.user_id):
			frappe.throw(_("User account {0} does not exist.").format(distributor_doc.user_id))

		user_doc = frappe.get_doc("User", distributor_doc.user_id)
		
		# Check if user is enabled
		if not user_doc.enabled:
			frappe.throw(_("User account is disabled. Please enable it first."))

		# Generate new reset password link
		reset_password_link = user_doc.reset_password(send_email=False)

		# Get email template
		subject, message = get_distributor_initial_email_template(distributor_doc, email, reset_password_link)

		# Send email
		frappe.sendmail(
			recipients=[email],
			sender=get_default_sender(),
			subject=subject,
			message=message,
			now=True
		)

		# Update credentials sent date and reset reminder count
		distributor_doc.db_set("credentials_sent_date", frappe.utils.now_datetime())
		distributor_doc.db_set("login_reminder_count", 0)

		return {
			"status": "success",
			"message": f"Email resent successfully to {distributor_doc.attendee_name or distributor_doc.distributor_name}"
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Resend Email Failed")
		frappe.throw(_("An error occurred while resending email: {0}").format(str(e)))

@frappe.whitelist()
def bulk_resend_emails_to_distributors(distributor_ids, filters=None):
	"""
	Resend initial emails to multiple distributors who already have user accounts.
	distributor_ids: List of distributor IDs to resend emails for
	filters: Optional filters used to select these distributors (for logging)
	"""
	frappe.only_for(["Administrator", "Supervisor", "System User"])

	if isinstance(distributor_ids, str):
		distributor_ids = frappe.parse_json(distributor_ids)

	if isinstance(filters, str):
		filters = frappe.parse_json(filters)

	results = {
		"success": [],
		"errors": [],
		"skipped": [],
		"total": len(distributor_ids)
	}

	for distributor_id in distributor_ids:
		try:
			distributor_doc = frappe.get_doc("Distributor", distributor_id)
			email = distributor_doc.distributor_email_address

			# Check if distributor has user_id
			if not distributor_doc.user_id:
				results["skipped"].append({
					"distributor_id": distributor_id,
					"name": distributor_doc.attendee_name or distributor_doc.distributor_name,
					"email": email,
					"message": "Distributor does not have a user account"
				})
				continue

			# Check if user exists
			if not frappe.db.exists("User", distributor_doc.user_id):
				results["skipped"].append({
					"distributor_id": distributor_id,
					"name": distributor_doc.attendee_name or distributor_doc.distributor_name,
					"email": email,
					"message": "User account does not exist"
				})
				continue

			user_doc = frappe.get_doc("User", distributor_doc.user_id)
			
			# Check if user is enabled
			if not user_doc.enabled:
				results["skipped"].append({
					"distributor_id": distributor_id,
					"name": distributor_doc.attendee_name or distributor_doc.distributor_name,
					"email": email,
					"message": "User account is disabled"
				})
				continue

			# Resend the email using the single function
			resend_initial_email_to_distributor(distributor_id)

			results["success"].append({
				"distributor_id": distributor_id,
				"name": distributor_doc.attendee_name or distributor_doc.distributor_name,
				"email": email,
				"message": "Email resent successfully"
			})

		except Exception as e:
			results["errors"].append({
				"distributor_id": distributor_id,
				"name": getattr(frappe.get_doc("Distributor", distributor_id), 'attendee_name', distributor_id),
				"error": str(e)
			})
			frappe.log_error(f"Failed to resend email for distributor {distributor_id}: {str(e)}", "Bulk Email Resend Error")

	# Send summary email to admins
	if results["success"] or results["errors"]:
		send_bulk_resend_summary_email(results, filters)

	return results

@frappe.whitelist()
def create_user_from_distributor(distributor_id):
	frappe.only_for(["Administrator", "Supervisor", "System User"])

	distributor_doc = frappe.get_doc("Distributor", distributor_id)
	email = distributor_doc.distributor_email_address
	country = distributor_doc.country

	print("email", email, "country", country)

	try:
		if not frappe.db.exists("User", email):
			new_password = generate_password()

			if not distributor_doc.user_id:
				# Create the user
				user = frappe.get_doc({
					"doctype": "User",
					"email": email,
					"enabled": 1,
					"user_type": "Website User",
					"send_welcome_email": 0,
					"mobile_no": distributor_doc.distributor_contact_number,
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
				distributor_doc.db_set("user_id", user.name)

				# Generate reset password link for the user
				reset_password_link = user.reset_password(send_email=False)

				# Set credentials sent date when user is created and email is sent
				distributor_doc.db_set("credentials_sent_date", frappe.utils.now_datetime())
				distributor_doc.db_set("is_active_user", 1)
				distributor_doc.db_set("login_reminder_count", 0)

				# Find LMS Course(s) where custom_assigned_to_role is "Distributor" or "All" and Option Country includes distributor's country
				distributor_courses = []
				for course in frappe.get_all(
					"LMS Course",
					filters={
						"custom_assigned_to_role": ["in", ["Distributor", "All"]],
						"published": 1
					},
					fields=["name", "title", "short_introduction"]
				):
					# Check if distributor's country is in the course's assigned countries via Option Country child table
					assigned_countries = frappe.get_all(
						"Option Country",
						filters={
							"parent": course["name"],
							"parenttype": "LMS Course",
							"country": country
						},
						pluck="country"
					)
					if assigned_countries:
						distributor_courses.append(course)

				# Use the first matching course, or set empty if none found
				if distributor_courses:
					distributor_course = distributor_courses[0]["title"]
					distributor_course_intro = distributor_courses[0]["short_introduction"]
				else:
					distributor_course = ""
					distributor_course_intro = ""

				subject, message = get_distributor_initial_email_template(distributor_doc, email, reset_password_link)

				frappe.sendmail(
					recipients=[email],
					sender=get_default_sender(),
					subject=subject,
					message=message,
					now=True
				)
				
				# Send email notification to admins about new distributor creation
				admins = frappe.get_all("User", 
					filters={"role_profile_name": "System Manager", "enabled": 1}, 
					pluck="email")
				
				if admins:
					subject = f"🎯 New Distributor Created: {distributor_doc.attendee_name} - Ethics & Compliance Training on HCP/HCO Interactions"
					message = f"<p>New distributor <b>{distributor_doc.attendee_name}</b> from <b>{distributor_doc.distributor_company_name}</b> has been created and credentials sent.</p><p>📧 Email: {email}</p><p>📅 Credentials sent: {frappe.utils.format_datetime(frappe.utils.now_datetime())}</p><p>🔔 Daily login reminders will start tomorrow if no login occurs.</p>"
					
					frappe.sendmail(
						recipients=admins,
						sender=get_default_sender(),
						subject=subject,
						message=message
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

# direct distributor redirect to /edit-distributor-profile page if he have "Can Edit Own Profile" role.
def user_after_login():
	user = frappe.session.user
	
	is_distributor = frappe.db.exists("Distributor", {"user_id": user})
	roles = frappe.get_roles(user)
	print(roles)
	if is_distributor and "Distributor" in roles and "Can Edit Own Profile" in roles:
			print("condition called")
			frappe.local.response["home_page"] = "/edit-distributor-profile"


def on_login(login_manager):
	user_id = login_manager.user

	# Keep existing default app redirect
	default_app = frappe.db.get_single_value("System Settings", "default_app")
	if default_app == "lms":
		frappe.local.response["home_page"] = "/lms"

	# Add distributor login tracking
	distributor = frappe.db.exists("Distributor", {"user_id": user_id})
	if distributor:
		now = frappe.utils.now_datetime()
		
		# Get current values
		first_login = frappe.db.get_value("Distributor", distributor, "first_login_date")
		
		# Always update last login date and mark as active
		frappe.db.set_value("Distributor", distributor, {
			"last_login_date": now,
			"is_active_user": 1
		})
		
		# Set first login if not already set
		if not first_login:
			frappe.db.set_value("Distributor", distributor, "first_login_date", now)
			
			# Send email notification for first login
			distributor_doc = frappe.get_doc("Distributor", distributor)
			
			# Send email to admins about first login
			admins = frappe.get_all("User", 
				filters={"role_profile_name": "System Manager", "enabled": 1}, 
				pluck="email")
			
			if admins:
				subject = f"✅ Distributor {distributor_doc.attendee_name} logged in for the first time - Ethics & Compliance Training on HCP/HCO Interactions"
				message = f"<p>Great news! Distributor <b>{distributor_doc.attendee_name}</b> from <b>{distributor_doc.distributor_company_name}</b> has successfully logged in for the first time.</p><p>📅 First Login: {frappe.utils.format_datetime(now)}</p><p>🎯 No more reminders needed for this distributor.</p>"
				
				frappe.sendmail(
					recipients=admins,

					sender=get_default_sender(),

					subject=subject,
					message=message
				)
			
		frappe.db.commit()
			
	frappe.local.response["redirect_to"] = "/lms"


@frappe.whitelist()
def send_daily_login_reminders():
	"""
	Send daily login reminders to distributors who haven't logged in yet.
	This function should be called by scheduler daily.
	"""
	
	# Get all distributors who haven't logged in yet and have user accounts
	distributors_needing_reminders = frappe.db.sql("""
		SELECT 
			d.name as distributor_id,
			d.attendee_name,
			d.distributor_company_name,
			d.distributor_email_address,
			d.user_id,
			d.credentials_sent_date,
			d.login_reminder_count,
			DATEDIFF(NOW(), d.credentials_sent_date) as days_since_creation
		FROM `tabDistributor` d
		WHERE 
			d.first_login_date IS NULL 
			AND d.user_id IS NOT NULL 
			AND d.user_id != ''
			AND d.credentials_sent_date IS NOT NULL
			AND DATEDIFF(NOW(), d.credentials_sent_date) >= 1
		ORDER BY d.credentials_sent_date ASC
	""", as_dict=True)
	
	if not distributors_needing_reminders:
		frappe.logger().info("No distributors need login reminders today")
		return {"status": "success", "message": "No distributors need reminders", "count": 0}
	
	reminders_sent = 0
	
	for distributor in distributors_needing_reminders:
		try:
			# Increment reminder count
			current_count = distributor.login_reminder_count or 0
			new_count = current_count + 1
			
			# Determine reminder urgency based on days and count
			days_since = distributor.days_since_creation
			
			if days_since <= 3:
				urgency = "gentle"
				subject_prefix = "👋 Gentle Reminder"
			elif days_since <= 7:
				urgency = "moderate" 
				subject_prefix = "⏰ Important Reminder"
			elif days_since <= 14:
				urgency = "urgent"
				subject_prefix = "🚨 Urgent Reminder"
			else:
				urgency = "final"
				subject_prefix = "⚠️ Final Reminder"
			
			# Create personalized reminder message
			subject = f"{subject_prefix}: Please login to Meril Learning Portal - Ethics & Compliance Training on HCP/HCO Interactions"
			
			message_content = get_login_reminder_message(
				distributor.attendee_name,
				distributor.distributor_company_name,
				days_since,
				new_count,
				urgency
			)
			
			# Send email to the distributor
			# Send email
			frappe.sendmail(
				recipients=[distributor.distributor_email_address],
				sender=get_default_sender(),
				subject=subject + " - Ethics & Compliance Training on HCP/HCO Interactions",
				message=message_content
			)
			# Also create a notification log for the distributor user
			if distributor.user_id:
				frappe.get_doc({
					"doctype": "Notification Log",
					"subject": subject,
					"email_content": message_content,
					"for_user": distributor.user_id,
					"type": "Alert"
				}).insert(ignore_permissions=True)

			
			# Update reminder count in distributor record
			frappe.db.set_value("Distributor", distributor.distributor_id, "login_reminder_count", new_count)
			
			# If it's been more than 30 days, also notify admins
			if days_since >= 30:
				admin_subject = f"⚠️ Distributor {distributor.attendee_name} hasn't logged in for {days_since} days - Ethics & Compliance Training on HCP/HCO Interactions"
				admin_message = f"<p>Distributor <b>{distributor.attendee_name}</b> from <b>{distributor.distributor_company_name}</b> has not logged in for <b>{days_since} days</b>.</p><p>📧 {new_count} reminders have been sent.</p><p>🎯 Consider manual follow-up or account review. Ethics & Compliance Training on HCP/HCO Interactions</p>"
				
				admins = frappe.get_all("User", 
					filters={"role_profile_name": "System Manager", "enabled": 1}, 
					pluck="email")
				
				if admins:
					frappe.sendmail(
						recipients=admins,
						sender=get_default_sender(),
						subject=admin_subject,
						message=admin_message
					)
			
			reminders_sent += 1
			frappe.logger().info(f"Login reminder sent to {distributor.attendee_name} (Day {days_since}, Reminder #{new_count})")
			
		except Exception as e:
			frappe.log_error(f"Failed to send login reminder to {distributor.attendee_name}: {str(e)}", "Login Reminder Error")
			continue
	
	# Commit all changes
	frappe.db.commit()
	
	return {
		"status": "success", 
		"message": f"Login reminders sent to {reminders_sent} distributors",
		"count": reminders_sent
	}


def get_login_reminder_message(name, company, days_since, reminder_count, urgency):
	"""Generate personalized login reminder message based on urgency level"""
	
	base_message = f"""
	<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
		<h2 style="color: #2c3e50;">Hello {name}!</h2>
		<p>We hope this message finds you well. This is a friendly reminder about your <b>Meril Learning Portal</b> account.</p>
	"""
	
	if urgency == "gentle":
		specific_message = f"""
		<p>🎯 Your account was created <b>{days_since} day(s) ago</b>, and we're excited to have you join our learning community!</p>
		<p>To get started with your training modules and resources, please login to your account using the credentials sent to you.</p>
		"""
	elif urgency == "moderate":
		specific_message = f"""
		<p>⏰ It's been <b>{days_since} days</b> since your account was created. We want to ensure you don't miss out on important training materials.</p>
		<p>Your learning journey is waiting! Please take a moment to login and explore the available courses.</p>
		"""
	elif urgency == "urgent":
		specific_message = f"""
		<p>🚨 <b>Urgent Action Required:</b> It's been <b>{days_since} days</b> since your account was created.</p>
		<p>To ensure compliance with training requirements and avoid any delays, please login to your account immediately.</p>
		"""
	else:  # final
		specific_message = f"""
		<p>⚠️ <b>Final Reminder:</b> Your account has been inactive for <b>{days_since} days</b>.</p>
		<p>This is our final automated reminder. If you don't login soon, your account may require manual reactivation.</p>
		<p>Please contact support if you're experiencing any login issues.</p>
		"""
	
	footer_message = f"""
		<div style="background-color: #f8f9fa; padding: 15px; margin: 20px 0; border-left: 4px solid #007bff;">
			<h3 style="margin: 0; color: #007bff;">🚀 Quick Login Steps:</h3>
			<ol style="margin: 10px 0;">
				<li>Go to the Meril Learning Portal</li>
				<li>Use your email: <b>{company}</b></li>
				<li>Enter the password sent in your welcome email</li>
				<li>Start exploring your personalized learning path!</li>
			</ol>
		</div>
		
		<p style="margin-top: 30px;">
			<strong>Need Help?</strong><br>
			If you're having trouble logging in or can't find your password, please contact our support team.
		</p>
		
		<p style="color: #6c757d; font-size: 12px; margin-top: 30px;">
			This is reminder #{reminder_count} • Company: {company} • Days since account creation: {days_since}
		</p>
	</div>
	"""
	
	return base_message + specific_message + footer_message


@frappe.whitelist()
def send_daily_course_reminders():
	"""
	Send daily course completion reminders to users who haven't completed their enrolled courses.
	This function should be called by scheduler daily.
	"""
	
	print("get_course reimder reached")
	# Get all users with incomplete enrolled courses
	incomplete_enrollments = frappe.db.sql("""
		SELECT 
			e.name as enrollment_id,
			e.member as user_id,
			e.course,
			e.creation as enrollment_date,
			c.title as course_title,
			c.short_introduction as course_introduction,
			u.full_name as user_name,
			u.email as user_email,
			u.name as user_name,
			e.progress,
			e.course_reminder_count,
			DATEDIFF(NOW(), e.creation) as days_since_enrollment
		FROM `tabLMS Enrollment` e
		JOIN `tabLMS Course` c ON e.course = c.name
		JOIN `tabUser` u ON e.member = u.name
		WHERE 
			e.completed_on IS NULL
			AND e.member IS NOT NULL
			AND DATEDIFF(NOW(), e.creation) >= 1
			AND u.enabled = 1
		ORDER BY e.creation ASC
	""", as_dict=True)
	
	if not incomplete_enrollments:
		frappe.logger().info("No users need course completion reminders today")
		return {"status": "success", "message": "No users need course reminders", "count": 0}
	
	reminders_sent = 0
	

	for enrollment in incomplete_enrollments:
		try:
			# Increment reminder count
			current_count = enrollment.course_reminder_count or 0
			new_count = current_count + 1
			user = enrollment.user_name
			# Check if the user is a distributor by looking up the user_id in Distributor records
			is_distributor = False

			days_since = enrollment.days_since_enrollment
			progress = enrollment.progress or 0
			if days_since <= 7:
				urgency = "gentle"
				subject_prefix = "📚 Gentle Reminder"
			elif days_since <= 14:
				urgency = "moderate" 
				subject_prefix = "⏰ Course Reminder"
			elif days_since <= 30:
				urgency = "urgent"
				subject_prefix = "🚨 Important Course Reminder"
			else:
				urgency = "final"
				subject_prefix = "⚠️ Final Course Reminder"
			
			# Create personalized reminder message
			subject = f"{subject_prefix}: Complete your course - Ethics & Compliance Training on HCP/HCO Interactions"

			is_distributor = frappe.db.exists("Distributor", {"user_id": user})
			is_employee = frappe.db.exists("Employee", {"user_id": user})
			for_role = "Administrator"
			attendee_name = None

			if is_distributor:
				subject = f"Reminder {new_count} : Ethics & Compliance Training on HCP/HCO Interactions"
				for_role = "Distributor"
				# Get attendee_name from Distributor
				attendee_name = frappe.db.get_value("Distributor", {"user_id": user}, "attendee_name")
			elif is_employee:
				subject = f"Reminder {new_count} Ethics & Compliance Training on HCPs/HCOs Interactions."
				for_role = "Employee"
				# Get employee_name from Employee
				attendee_name = frappe.db.get_value("Employee", {"user_id": user}, "employee_name")

			name = attendee_name if attendee_name else enrollment.user_name
			# Determine reminder urgency based on days and count
			days_since = enrollment.days_since_enrollment
			progress = enrollment.progress or 0
			
	
			
			message_content = get_course_reminder_message(	
				for_role,
				name,
				enrollment.course_title,
				enrollment.course_intrudoction,
				days_since,
				progress,
				new_count,
				urgency
			)
			
			# Send email to the user
			frappe.sendmail(
				recipients=[enrollment.user_email],
				sender=get_default_sender(),
				subject=subject,
				message=message_content
			)
			# Create notification log for the user
			frappe.get_doc({
				"doctype": "Notification Log",
				"subject": subject,
				"email_content": message_content,
				"for_user": enrollment.user_name,
				"type": "Alert",
				"document_type": "LMS Enrollment",
				"document_name": enrollment.enrollment_id,
			}).insert(ignore_permissions=True)
			
			# Update reminder count in enrollment record
			frappe.db.set_value("LMS Enrollment", enrollment.enrollment_id, "course_reminder_count", new_count)
			
			# If it's been more than 45 days, also notify admins
			if days_since >= 45:
				admin_subject = f"⚠️ User {enrollment.user_name} hasn't completed course for {days_since} days - Ethics & Compliance Training on HCP/HCO Interactions"
				admin_message = f"<p>User <b>{enrollment.user_name}</b> enrolled in <b>{enrollment.course_title}</b> has not completed the course for <b>{days_since} days</b>.</p><p>📊 Current progress: {progress}%</p><p>📧 {new_count} reminders have been sent.</p><p>🎯 Consider manual follow-up or course review.</p>"
				
				admins = frappe.get_all("User", 
					filters={"role_profile_name": "System Manager", "enabled": 1}, 
					pluck="email")
				
				if admins:
					frappe.sendmail(
						recipients=admins,
						sender=get_default_sender(),
						subject=admin_subject,
						message=admin_message
					)
			
			reminders_sent += 1
			frappe.logger().info(f"Course reminder sent to {enrollment.user_name} for {enrollment.course_title} (Day {days_since}, Reminder #{new_count})")
			
		except Exception as e:
			print("error", str(e))
			frappe.log_error(f"Failed to send course reminder to {enrollment.user_name}: {str(e)}", "Course Reminder Error")
			continue
	
	# Commit all changes
	frappe.db.commit()
	
	return {
		"status": "success", 
		"message": f"Course reminders sent to {reminders_sent} users",
		"count": reminders_sent
	}


def get_course_reminder_message(for_role, name, course_title, course_introduction, days_since, progress, reminder_count, urgency):
	"""Generate personalized course completion reminder message based on urgency level"""
	
	if for_role == "Distributor":
		return f'''<p>Dear {name},</p>

		<p>This is a kind reminder to complete the <span style="font-weight:bold">{course_title} on {course_introduction},</span>. Our records indicate that the training is still pending. </p>

		
		<p>For login details, please refer to the email sent to you with the subject line ‘Ethics & Compliance Training on HCP/HCO Interactions’.</p>
		
			<p style="font-weight: bold; margin-left: 10px;"><span style="margin-right: 10px;">•</span> Please click on the below link to log in:</p>
			<a href="{frappe.utils.get_url("/login")}">{frappe.utils.get_url("/login")}</a>
		<p>Kindly treat this as a priority and complete the training at your earliest.</p>

		<p>Best regards,</p>
		<p>Meril</p>'''
	elif for_role == "Employee":
		login_url = frappe.utils.get_url("/login")
		return f"""<p>Dear {name},</p>

<p>This is a kind reminder to complete the <span style="font-weight:bold;">Ethics & Compliance Training on HCPs/HCOs Interactions.</span> Our records indicate that the training is still pending.</p>

<p>For login details, please refer to the email sent to you with the subject line 'Ethics & Compliance Training on HCPs/HCOs Interactions'.</p>

<p>Please click on the below link to log in:</p>
<p>(<a href="{login_url}">{login_url}</a>)</p>

<p>Kindly treat this as a priority and complete the training at your earliest.</p>

<p>Best regards,</p>
<p>Meril</p>"""

	base_message = f"""
	<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
		<h2 style="color: #2c3e50;">Hello {name}!</h2>
		<p>We hope you're enjoying your learning journey on the <b>Meril Learning Portal</b>.</p>
	"""
	
	if urgency == "gentle":
		specific_message = f"""
		<p>📚 You enrolled in <b>{course_title}</b> <b>{days_since} day(s) ago</b> and we wanted to check on your progress!</p>
		<p>You've completed <b>{progress}%</b> of the course. Keep up the great work and continue when you have time.</p>
		"""
	elif urgency == "moderate":
		specific_message = f"""
		<p>⏰ It's been <b>{days_since} days</b> since you enrolled in <b>{course_title}</b>.</p>
		<p>You're currently at <b>{progress}%</b> completion. We encourage you to continue your learning journey to get the most out of this course.</p>
		"""
	elif urgency == "urgent":
		specific_message = f"""
		<p>🚨 <b>Important Reminder:</b> Your enrollment in <b>{course_title}</b> has been active for <b>{days_since} days</b>.</p>
		<p>Current progress: <b>{progress}%</b>. To ensure you meet your learning objectives, please prioritize completing this course.</p>
		"""
	else:  # final
		specific_message = f"""
		<p>⚠️ <b>Final Course Reminder:</b> You've been enrolled in <b>{course_title}</b> for <b>{days_since} days</b>.</p>
		<p>Progress: <b>{progress}%</b>. This is our final automated reminder. Please complete the course to maintain your learning track record.</p>
		<p>If you're facing any difficulties, please contact our support team.</p>
		"""
	
	footer_message = f"""
		<div style="background-color: #f8f9fa; padding: 15px; margin: 20px 0; border-left: 4px solid #007bff;">
			<h3 style="margin: 0; color: #007bff;">🚀 Continue Learning:</h3>
			<ol style="margin: 10px 0;">
				<li>Log in to the Meril Learning Portal</li>
				<li>Navigate to your enrolled courses</li>
				<li>Continue from where you left off</li>
				<li>Complete the course to earn your certificate!</li>
			</ol>
		</div>
		
		<div style="background-color: #e7f3ff; padding: 15px; margin: 20px 0; border-radius: 5px;">
			<h4 style="margin: 0 0 10px 0; color: #0066cc;">📊 Your Progress:</h4>
			<div style="background-color: #fff; border-radius: 10px; height: 20px; overflow: hidden;">
				<div style="background-color: #28a745; height: 100%; width: {progress}%; transition: width 0.3s ease;"></div>
			</div>
			<p style="margin: 5px 0 0 0; font-size: 14px; color: #333;">{progress}% Complete</p>
		</div>
		
		<p style="margin-top: 30px;">
			<strong>Need Help?</strong><br>
			If you're having trouble accessing the course or need assistance, please contact our support team.
		</p>
		
		<p style="color: #6c757d; font-size: 12px; margin-top: 30px;">
			This is reminder #{reminder_count} • Course: {course_title} • Days since enrollment: {days_since}
		</p>
	</div>
	"""
	
	return base_message + specific_message + footer_message


@frappe.whitelist(allow_guest=False)
def get_distributor_profile(user_id=None):
	user_name = frappe.session.user
	user_doc = frappe.get_doc("User", {"name": frappe.session.user})
	roles = [role.role for role in user_doc.roles]

	if "Distributor" not in roles:
		frappe.local.response["home_page"] = "/lms"
		frappe.throw("User is not a distributor")

	
	can_edit_own_profile = "Can Edit Own Profile" in roles
	
	if not can_edit_own_profile:
		frappe.local.response["home_page"] = "/lms"
		frappe.local.response["message"] = "You have already updated your profile."
		return None
		
	fields = [ 
		"name",
		"bu__fd_head",
		"rsm__state_head",
		"region",
		"state",
		"city",
		"account__distributor_code",
		"distributor_email_address",
		"distributor_company_address",
		"distributor_contact_number",
		"attendee_name",
		"designation",
		"country",
		"distributor_name",
		"distributor_company_name"
	]
	distributor = frappe.db.get_value("Distributor", {"user_id": user_name }, fields, as_dict=True)
	
	# Get the child table data separately
	if distributor:
		meril_company_table = frappe.get_all(
			"Meril Distributor Division Child",
			filters={"parent": distributor.name},
			fields=["division", "meril_company_name", "rsm", "bu_head", "distributor_code"]
		)
		
		distributor["meril_company_table"] = meril_company_table
		
	
	if distributor and not can_edit_own_profile:
		frappe.local.response["home_page"] = "/lms"
		return None
	else:
		frappe.local.response["home_page"] = "/edit-distributor-profile"

	# Also set department name and company names for options for Meril company table

	# Get array of dict of department name and its related company name
	department_company_list = frappe.get_all(
		"Department",
		filters={},
		fields=["name", "company"],
		order_by="name asc"
	)

	country_list = frappe.get_all(
		"Country",
		filters={},
		fields=["country_name"],
		order_by="country_name asc"
	)
	distributor["country_list"] = [c["country_name"] for c in country_list]

	distributor["department_company_list"] = department_company_list
	return distributor

@frappe.whitelist(allow_guest=False)
def update_distributor_profile(data):

	
    data = json.loads(data)
    user_id = frappe.session.user
    user_doc = frappe.get_doc("User", user_id)
    roles = [role.role for role in user_doc.roles]
    can_edit_own_profile = "Can Edit Own Profile" in roles

    if "Distributor" not in roles:
        frappe.local.response["redirect"] = "/lms"
        return

    distributor = frappe.get_doc("Distributor", {"user_id": user_id})
    if "Distributor" in roles and not can_edit_own_profile :
        frappe.local.response["redirect"] = "/lms"
        return
    elif distributor and not can_edit_own_profile: 
        frappe.local.response["redirect"] = "/lms"
        return
    else:
        filter_data = [
            "region",
            "state", "city", "account__distributor_code", "distributor_company_name",
            "distributor_email_address", "distributor_company_address", "distributor_contact_number", "attendee_name", "designation", "distributor_name", "country"
        ]
        filtered_data = {}
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


@frappe.whitelist()
def send_manual_login_reminder(distributor_id):
	"""
	Send a manual login reminder to a specific distributor.
	This function is called from the dashboard for manual reminders.
	"""
	
	try:
		# Get distributor details
		distributor = frappe.get_doc("Distributor", distributor_id)
		
		# Check if distributor has already logged in
		if distributor.first_login_date:
			return {"status": "error", "message": "Distributor has already logged in"}
		
		if not distributor.user_id:
			return {"status": "error", "message": "Distributor has no user account"}
		
		# Increment reminder count
		current_count = distributor.login_reminder_count or 0
		new_count = current_count + 1
		
		# Get days since credentials were sent
		days_since = 0
		if distributor.credentials_sent_date:
			from datetime import datetime
			credentials_date = frappe.utils.get_datetime(distributor.credentials_sent_date)
			now = frappe.utils.now_datetime()
			days_since = (now - credentials_date).days
		
		# Determine urgency based on days and count
		if days_since <= 3:
			urgency = "gentle"
			subject_prefix = "👋 Manual Reminder"
		elif days_since <= 7:
			urgency = "moderate" 
			subject_prefix = "⏰ Manual Reminder"
		elif days_since <= 14:
			urgency = "urgent"
			subject_prefix = "🚨 Manual Reminder"
		else:
			urgency = "final"
			subject_prefix = "⚠️ Manual Reminder"
		
		# Create personalized reminder message
		subject = f"{subject_prefix}: Please login to Meril Learning Portal"
		
		message_content = get_login_reminder_message(
			distributor.attendee_name,
			distributor.distributor_company_name,
			days_since,
			new_count,
			urgency
		)
		
		# Add manual reminder note
		message_content += f"""
		<div style="border-top: 1px solid #ddd; margin-top: 20px; padding-top: 15px; font-size: 12px; color: #666;">
			<p><strong>Note:</strong> This is a manual reminder sent by an administrator.</p>
		</div>
		"""
		
		# Send email to the distributor
		frappe.sendmail(
			recipients=[distributor.distributor_email_address],
			sender=get_default_sender(),
			subject=subject + " - Ethics & Compliance Training on HCP/HCO Interactions",
			message=message_content
		)
		
		# Update reminder count
		frappe.db.set_value("Distributor", distributor_id, "login_reminder_count", new_count)
		frappe.db.commit()
		
		return {
			"status": "success", 
			"message": f"Manual reminder sent to {distributor.attendee_name}",
			"reminder_count": new_count
		}
		
	except Exception as e:
		frappe.log_error(f"Failed to send manual reminder to {distributor_id}: {str(e)}", "Manual Reminder Error")
		return {"status": "error", "message": str(e)}


@frappe.whitelist()
def send_manual_course_reminder(enrollment_id):
	"""
	Send a manual course completion reminder to a specific user.
	This function is called from the dashboard for manual reminders.
	"""
	
	try:
		# Get enrollment details
		enrollment = frappe.get_doc("LMS Enrollment", enrollment_id)
		
		# Check if course is already completed
		if enrollment.completed_on:
			return {"status": "error", "message": "Course is already completed"}
		
		user = frappe.get_doc("User", enrollment.member)
		course = frappe.get_doc("LMS Course", enrollment.course)
		
		# Increment reminder count
		current_count = enrollment.course_reminder_count or 0
		new_count = current_count + 1
		
		# Get days since enrollment
		days_since = 0
		if enrollment.creation:
			from datetime import datetime
			enrollment_date = frappe.utils.get_datetime(enrollment.creation)
			now = frappe.utils.now_datetime()
			days_since = (now - enrollment_date).days
		
		# Determine urgency based on days and count
		if days_since <= 7:
			urgency = "gentle"
			subject_prefix = "📚 Manual Reminder"
		elif days_since <= 14:
			urgency = "moderate" 
			subject_prefix = "⏰ Manual Reminder"
		elif days_since <= 30:
			urgency = "urgent"
			subject_prefix = "🚨 Manual Reminder"
		else:
			urgency = "final"
			subject_prefix = "⚠️ Manual Reminder"
		
		# Create personalized reminder message
		subject = f"{subject_prefix}: Complete your course - {course.title}"
		
		message_content = get_course_reminder_message(
			None,
			user.full_name,
			course.title,
			None,
			days_since,
			enrollment.progress or 0,
			new_count,
			urgency
		)
		
		# Add manual reminder note
		message_content += f"""
		<div style="border-top: 1px solid #ddd; margin-top: 20px; padding-top: 15px; font-size: 12px; color: #666;">
			<p><strong>Note:</strong> This is a manual reminder sent by an administrator.</p>
		</div>
		"""
		
		# Send email to the user
		frappe.sendmail(
			recipients=[user.email],
			sender=get_default_sender(),
			subject=subject,
			message=message_content
		)
		# Create notification log for the user
		frappe.get_doc({
			"doctype": "Notification Log",
			"subject": subject,
			"email_content": message_content,
			"for_user": user.name,
			"type": "Alert",
			"document_type": "LMS Enrollment",
			"document_name": enrollment_id,
		}).insert(ignore_permissions=True)
		
		# Update reminder count
		frappe.db.set_value("LMS Enrollment", enrollment_id, "course_reminder_count", new_count)
		frappe.db.commit()
		
		return {
			"status": "success", 
			"message": f"Manual course reminder sent to {user.full_name}",
			"reminder_count": new_count
		}
		
	except Exception as e:
		frappe.log_error(f"Failed to send manual course reminder for {enrollment_id}: {str(e)}", "Manual Course Reminder Error")
		return {"status": "error", "message": str(e)}


def create_user_from_distributor_hook(doc, _method):
	try:
		# Check if automatic user creation is enabled
		lms_settings = frappe.get_single("LMS Settings")
		if not getattr(lms_settings, "auto_create_distributor_users", False):
			frappe.logger().info(f"Automatic user creation is disabled for distributor: {doc.name}")
			return

		# doc is a Distributor document; pass its name to the API
		create_user_from_distributor(doc.name)
	except Exception as e:
		# Log but do not block Distributor creation
		frappe.log_error(f"create_user_from_distributor_hook failed: {str(e)}")
		return


def send_bulk_creation_summary_email(results, filters):
	"""Send summary email to admins about bulk user creation results"""

	admins = frappe.get_all("User",
		filters={"role_profile_name": "System Manager", "enabled": 1},
		pluck="email")

	if not admins:
		return

	success_count = len(results["success"])
	error_count = len(results["errors"])
	exists_count = len(results["already_exists"])
	total_count = results["total"]

	subject = f"📊 Bulk User Creation Summary: {success_count} Created, {error_count} Errors"

	message = f"""
	<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
		<h2 style="color: #2c3e50;">Bulk Distributor User Creation Summary</h2>

		<div style="background-color: #f8f9fa; padding: 15px; margin: 20px 0; border-radius: 5px;">
			<h3 style="margin: 0 0 10px 0; color: #007bff;">📈 Summary Statistics</h3>
			<p><strong>Total Processed:</strong> {total_count}</p>
			<p><strong>✅ Successfully Created:</strong> {success_count}</p>
			<p><strong>⚠️ Already Existed:</strong> {exists_count}</p>
			<p><strong>❌ Errors:</strong> {error_count}</p>
		</div>
	"""

	if results["success"]:
		message += f"""
		<div style="background-color: #d4edda; padding: 15px; margin: 20px 0; border-radius: 5px; border-left: 4px solid #28a745;">
			<h3 style="margin: 0 0 10px 0; color: #155724;">✅ Successfully Created ({success_count})</h3>
			<ul style="margin: 5px 0;">
		"""
		for item in results["success"]:
			message += f"<li><strong>{item['name']}</strong> ({item['email']})</li>"
		message += "</ul></div>"

	if results["already_exists"]:
		message += f"""
		<div style="background-color: #fff3cd; padding: 15px; margin: 20px 0; border-radius: 5px; border-left: 4px solid #ffc107;">
			<h3 style="margin: 0 0 10px 0; color: #856404;">⚠️ Already Existed ({exists_count})</h3>
			<ul style="margin: 5px 0;">
		"""
		for item in results["already_exists"]:
			message += f"<li><strong>{item['name']}</strong> ({item['email']}) - {item['message']}</li>"
		message += "</ul></div>"

	if results["errors"]:
		message += f"""
		<div style="background-color: #f8d7da; padding: 15px; margin: 20px 0; border-radius: 5px; border-left: 4px solid #dc3545;">
			<h3 style="margin: 0 0 10px 0; color: #721c24;">❌ Errors ({error_count})</h3>
			<ul style="margin: 5px 0;">
		"""
		for item in results["errors"]:
			message += f"<li><strong>{item['name']}</strong> - {item['error']}</li>"
		message += "</ul></div>"

	if filters:
		message += f"""
		<div style="background-color: #e7f3ff; padding: 15px; margin: 20px 0; border-radius: 5px;">
			<h4 style="margin: 0 0 10px 0; color: #0066cc;">🔍 Applied Filters</h4>
			<pre style="background: #fff; padding: 10px; border-radius: 3px; font-size: 12px;">{frappe.as_json(filters, indent=2)}</pre>
		</div>
		"""

	message += f"""
		<p style="margin-top: 30px; color: #6c757d; font-size: 12px;">
			Bulk operation completed at {frappe.utils.format_datetime(frappe.utils.now_datetime())}
		</p>
	</div>
	"""

	frappe.sendmail(
		recipients=admins,
		sender=get_default_sender(),
		subject=subject,
		message=message
	)

def send_bulk_resend_summary_email(results, filters):
	"""Send summary email to admins about bulk email resend results"""

	admins = frappe.get_all("User",
		filters={"role_profile_name": "System Manager", "enabled": 1},
		pluck="email")

	if not admins:
		return

	success_count = len(results["success"])
	error_count = len(results["errors"])
	skipped_count = len(results["skipped"])
	total_count = results["total"]

	subject = f"📧 Bulk Email Resend Summary: {success_count} Sent, {error_count} Errors"

	message = f"""
	<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
		<h2 style="color: #2c3e50;">Bulk Distributor Email Resend Summary</h2>

		<div style="background-color: #f8f9fa; padding: 15px; margin: 20px 0; border-radius: 5px;">
			<h3 style="margin: 0 0 10px 0; color: #007bff;">📈 Summary Statistics</h3>
			<p><strong>Total Processed:</strong> {total_count}</p>
			<p><strong>✅ Successfully Sent:</strong> {success_count}</p>
			<p><strong>⚠️ Skipped:</strong> {skipped_count}</p>
			<p><strong>❌ Errors:</strong> {error_count}</p>
		</div>
	"""

	if results["success"]:
		message += f"""
		<div style="background-color: #d4edda; padding: 15px; margin: 20px 0; border-radius: 5px; border-left: 4px solid #28a745;">
			<h3 style="margin: 0 0 10px 0; color: #155724;">✅ Successfully Sent ({success_count})</h3>
			<ul style="margin: 5px 0;">
		"""
		for item in results["success"]:
			message += f"<li><strong>{item['name']}</strong> ({item['email']})</li>"
		message += "</ul></div>"

	if results["skipped"]:
		message += f"""
		<div style="background-color: #fff3cd; padding: 15px; margin: 20px 0; border-radius: 5px; border-left: 4px solid #ffc107;">
			<h3 style="margin: 0 0 10px 0; color: #856404;">⚠️ Skipped ({skipped_count})</h3>
			<ul style="margin: 5px 0;">
		"""
		for item in results["skipped"]:
			message += f"<li><strong>{item['name']}</strong> ({item['email']}) - {item['message']}</li>"
		message += "</ul></div>"

	if results["errors"]:
		message += f"""
		<div style="background-color: #f8d7da; padding: 15px; margin: 20px 0; border-radius: 5px; border-left: 4px solid #dc3545;">
			<h3 style="margin: 0 0 10px 0; color: #721c24;">❌ Errors ({error_count})</h3>
			<ul style="margin: 5px 0;">
		"""
		for item in results["errors"]:
			message += f"<li><strong>{item['name']}</strong> - {item['error']}</li>"
		message += "</ul></div>"

	if filters:
		message += f"""
		<div style="background-color: #e7f3ff; padding: 15px; margin: 20px 0; border-radius: 5px;">
			<h4 style="margin: 0 0 10px 0; color: #0066cc;">🔍 Applied Filters</h4>
			<pre style="background: #fff; padding: 10px; border-radius: 3px; font-size: 12px;">{frappe.as_json(filters, indent=2)}</pre>
		</div>
		"""

	message += f"""
		<p style="margin-top: 30px; color: #6c757d; font-size: 12px;">
			Bulk operation completed at {frappe.utils.format_datetime(frappe.utils.now_datetime())}
		</p>
	</div>
	"""

	frappe.sendmail(
		recipients=admins,
		sender=get_default_sender(),
		subject=subject,
		message=message
	)


@frappe.whitelist()
def send_re_enrollment_email(user_email, partner_name, user_id="123", password="234"):
	"""
	Send re-enrollment email notification to a user.
	This function sends the specific re-enrollment email with the provided content.
	"""
	try:
		# Get the user document to generate reset password link
		user_doc = frappe.get_doc("User", user_email)

		# Generate reset password link for the user (same as in initial email)
		reset_password_link = user_doc.reset_password(send_email=False)

		login_url = frappe.utils.get_url("/login")
		user_identifier = user_id or user_email

		subject = "Re-enrolled in Ethics & Compliance Training on HCPs/HCOs Interactions."

		message = f"""<p>Dear {partner_name},</p>

<p>In line with our mandatory training, you have been Re-enrolled for the <span style="font-weight:bold;">Ethics & Compliance Training on HCPs/HCOs Interactions.</span> This training is essential to ensure adherence to our ethical standards and regulatory guidelines.</p>

<p style="font-weight:bold;">Login Credentials:</p>
<p>Please click on the below link to log in:</p>
<p>(<a href="{login_url}">{login_url}</a>)</p>
<p>User ID: {user_identifier}</p>
<p>Password: (<a href="{reset_password_link}">Reset password</a>)</p>

<p>We kindly request you to complete this training at your earliest. Timely completion is important to maintain compliance and avoid any lapses in regulatory obligations.</p>

<p>Best regards,</p>
<p>Meril</p>"""

		# Send email
		frappe.sendmail(
			recipients=[user_email],
			sender=get_default_sender(),
			subject=subject,
			message=message
		)

		return {
			"status": "success",
			"message": f"Re-enrollment email sent to {user_email}"
		}

	except Exception as e:
		frappe.log_error(f"Failed to send re-enrollment email to {user_email}: {str(e)}", "Re-enrollment Email Error")
		return {
			"status": "error",
			"message": str(e)
		}

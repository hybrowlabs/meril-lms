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
						"mobile_no": self.cell_number,
						"send_welcome_email": 0,
					}
					).insert(ignore_permissions=True).email

				self.db_set("user_id", self.user_id)
				update_password(email, new_password)
				
				# Update self in the database
				frappe.sendmail(
					recipients=[self.company_email],	
					sender=get_default_sender(),
					subject='Test Email',	
					message=f'<p>Hello {self.first_name},<br><br>Your account for LMS has been created.<br><br>Email: {self.company_email}<br>Password: {new_password}<br><br>Please <a href="{frappe.utils.get_url("/login")}">click here to login</a>.<br><br>Thank you!</p>'
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
                
                # Set credentials sent date when user is created and email is sent
                self.db_set("credentials_sent_date", frappe.utils.now_datetime())
                self.db_set("is_active_user", 1)
                self.db_set("login_reminder_count", 0)

                frappe.sendmail(
                    recipients=[email],
                    sender=get_default_sender(),
                    subject='Your Merlin LMS Account',
                    message=f'<p>Hello {email},<br>Your password is: <b>{new_password}</b><br>You can log in at: <a href="{frappe.utils.get_url("/login")}">{frappe.utils.get_url("/login")}</a><br>Regards,<br>Merlin LMS</p>'
                )
                
                # Send email notification to admins about new distributor creation
                admins = frappe.get_all("User", 
                    filters={"role_profile_name": "System Manager", "enabled": 1}, 
                    pluck="email")
                
                if admins:
                    subject = f"🎯 New Distributor Created: {self.attendee_name}"
                    message = f"<p>New distributor <b>{self.attendee_name}</b> from <b>{self.distributor_company_name}</b> has been created and credentials sent.</p><p>📧 Email: {email}</p><p>📅 Credentials sent: {frappe.utils.format_datetime(frappe.utils.now_datetime())}</p><p>🔔 Daily login reminders will start tomorrow if no login occurs.</p>"
                    
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
				subject = f"✅ Distributor {distributor_doc.attendee_name} logged in for the first time"
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
			subject = f"{subject_prefix}: Please login to Meril Learning Portal"
			
			message_content = get_login_reminder_message(
				distributor.attendee_name,
				distributor.distributor_company_name,
				days_since,
				new_count,
				urgency
			)
			
			# Send email to the distributor
			frappe.sendmail(
				recipients=[distributor.distributor_email_address],

				sender=get_default_sender(),

				subject=subject,
				message=message_content
			)
			# Update reminder count in distributor record
			frappe.db.set_value("Distributor", distributor.distributor_id, "login_reminder_count", new_count)
			
			# If it's been more than 30 days, also notify admins
			if days_since >= 30:
				admin_subject = f"⚠️ Distributor {distributor.attendee_name} hasn't logged in for {days_since} days"
				admin_message = f"<p>Distributor <b>{distributor.attendee_name}</b> from <b>{distributor.distributor_company_name}</b> has not logged in for <b>{days_since} days</b>.</p><p>📧 {new_count} reminders have been sent.</p><p>🎯 Consider manual follow-up or account review.</p>"
				
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
	
	# Get all users with incomplete enrolled courses
	incomplete_enrollments = frappe.db.sql("""
		SELECT 
			e.name as enrollment_id,
			e.member as user_id,
			e.course,
			e.creation as enrollment_date,
			c.title as course_title,
			u.full_name as user_name,
			u.email as user_email,
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
			
			# Determine reminder urgency based on days and count
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
			subject = f"{subject_prefix}: Complete your course - {enrollment.course_title}"
			
			message_content = get_course_reminder_message(
				enrollment.user_name,
				enrollment.course_title,
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
			
			# Update reminder count in enrollment record
			frappe.db.set_value("LMS Enrollment", enrollment.enrollment_id, "course_reminder_count", new_count)
			
			# If it's been more than 45 days, also notify admins
			if days_since >= 45:
				admin_subject = f"⚠️ User {enrollment.user_name} hasn't completed course for {days_since} days"
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
			frappe.log_error(f"Failed to send course reminder to {enrollment.user_name}: {str(e)}", "Course Reminder Error")
			continue
	
	# Commit all changes
	frappe.db.commit()
	
	return {
		"status": "success", 
		"message": f"Course reminders sent to {reminders_sent} users",
		"count": reminders_sent
	}


def get_course_reminder_message(name, course_title, days_since, progress, reminder_count, urgency):
	"""Generate personalized course completion reminder message based on urgency level"""
	
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
	can_edit_own_profile = "Can Edit Own Profile" in roles
	
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
             "bu__fd_head", "rsm__state_head", "region",
            "state", "city", "account__distributor_code", "distributor_company_name",
            "distributor_email_address", "distributor_company_address", "distributor_contact_number", "attendee_name", "designation"
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
			subject=subject,
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
			user.full_name,
			course.title,
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





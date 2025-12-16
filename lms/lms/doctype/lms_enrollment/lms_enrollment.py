# Copyright (c) 2021, FOSS United and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import ceil, now, flt


class LMSEnrollment(Document):
	def validate(self):
		# Skip validation for re-enrollment to allow multiple enrollment records
		# for the same user/course combination (needed for re-enrollment functionality)
		if not getattr(self.flags, 'is_re_enrollment', False):
			self.validate_membership_in_same_batch()
			self.validate_membership_in_different_batch_same_course()
		else:
			# Log that validation was skipped for re-enrollment
			frappe.logger().info(f"Skipping enrollment validation for re-enrollment: {self.member} in course {self.course}")

	def on_update(self):
		self.update_program_progress()
		self.check_course_completion()

	def update_program_progress(self):
		update_program_progress(self.member)

	def before_save(self):
		"""Check if progress has changed and update completion status"""
		if self.has_value_changed("progress"):
			self.check_course_completion()

	def check_course_completion(self):
		"""Check if course is completed and update access restrictions"""
		# Skip completion check for admin and moderator roles
		if self.is_admin_or_moderator():
			return

		# Check if course is completed (100% progress)
		if self.progress and flt(self.progress) >= 100.0:
			self.mark_course_completed()
		elif self.completion_status == "Completed" and flt(self.progress or 0) < 100.0:
			# If completion status is marked as completed but progress is less than 100%
			# This might happen during re-enrollment, so update status accordingly
			if self.completion_status != "Re-enrolled":
				self.completion_status = "Active"
				self.access_restricted = 0

	def mark_course_completed(self):
		"""Mark the course as completed"""
		if self.completion_status != "Completed":
			self.completion_status = "Completed"
			# Restrict access for completed courses - as per requirement
			self.access_restricted = 1
			self.completed_on = now()

			# Log completion event
			frappe.logger().info(f"Course {self.course} completed by {self.member}")

	def is_admin_or_moderator(self):
		"""Check if the user has admin or moderator roles"""
		user_roles = frappe.get_roles(self.member)
		admin_roles = ["System Manager", "Administrator", "Supervisor"]
		return any(role in admin_roles for role in user_roles)

	def can_access_course(self):
		"""Check if user can access the course"""
		# Admin and moderators always have access
		if self.is_admin_or_moderator():
			return True

		# Check if access is restricted due to completion
		if self.access_restricted:
			return False

		return True

	def re_enroll_user(self, re_enrolled_by=None, reset_progress=True):
		"""Create a new enrollment record for re-enrollment while preserving history"""
		if not self.can_re_enroll(re_enrolled_by):
			frappe.throw(_("You don't have permission to re-enroll this user"))

		# Create new enrollment record instead of modifying existing
		new_enrollment = self.create_re_enrollment_record(re_enrolled_by)

		# Create fresh course documents for the new enrollment
		new_enrollment.create_fresh_course_documents()

		# Send re-enrollment email notification
		new_enrollment.send_re_enrollment_notification()

		frappe.logger().info(f"User {self.member} re-enrolled in course {self.course} by {re_enrolled_by}. New enrollment: {new_enrollment.name}")

		return new_enrollment

	def send_re_enrollment_notification(self):
		"""Send re-enrollment email notification to the user"""
		try:
			# Get user details
			user = frappe.get_doc("User", self.member)

			# Get user role and partner name
			user_roles = frappe.get_roles(self.member)
			partner_name = user.full_name
			user_id = user.email  # Use email as user ID

			# Check if user is a Distributor or Employee to get specific details
			if "Distributor" in user_roles:
				distributor_doc = frappe.get_doc("Distributor", {"user_id": self.member})
				partner_name = distributor_doc.attendee_name or distributor_doc.distributor_name or user.full_name
			elif "Employee" in user_roles:
				employee_doc = frappe.get_doc("Employee", {"user_id": self.member})
				partner_name = employee_doc.employee_name or user.full_name

			# Call the email function from user.py
			from lms.lms.user import send_re_enrollment_email
			result = send_re_enrollment_email(
				user_email=user.email,
				partner_name=partner_name,
				user_id=user_id
			)

			if result.get("status") == "success":
				frappe.logger().info(f"Re-enrollment email sent to {user.email}")
			else:
				frappe.logger().error(f"Failed to send re-enrollment email to {user.email}: {result.get('message')}")

		except Exception as e:
			frappe.log_error(f"Error sending re-enrollment notification: {str(e)}", "Re-enrollment Email Error")

	def can_re_enroll(self, user=None):
		"""Check if the given user can re-enroll this enrollment"""
		user = user or frappe.session.user
		user_roles = frappe.get_roles(user)

		# System Manager and Administrator can always re-enroll
		if "System Manager" in user_roles or "Administrator" in user_roles:
			return True

		# Moderators can re-enroll distributors and employees
		if "Supervisor" in user_roles:
			return True

		# Check if user is senior/manager of the enrolled member
		# This would require additional hierarchy logic based on your user structure
		if self.is_senior_of_member(user):
			return True

		return False

	def is_senior_of_member(self, potential_senior):
		"""Check if potential_senior is a senior of the enrolled member"""
		# This is a placeholder for hierarchy checking logic
		# You'll need to implement this based on your organizational structure
		# For example, checking if there's a "reports_to" field in User doctype
		# or checking role hierarchy in a custom doctype

		# Example implementation (customize as needed):
		member_reports_to = frappe.db.get_value("User", self.member, "reports_to")
		return member_reports_to == potential_senior

	def create_re_enrollment_record(self, re_enrolled_by):
		"""Create a new enrollment record for re-enrollment"""
		# Get the total re-enrollment count across all versions
		total_enrollments = frappe.db.count('LMS Enrollment', {
			'member': self.member,
			'course': self.course
		})

		# Get the original enrollment date from the first enrollment
		original_date = frappe.db.get_value(
			'LMS Enrollment',
			{'member': self.member, 'course': self.course},
			'original_enrollment_date',
			order_by='creation asc'
		)

		if not original_date:
			original_date = frappe.db.get_value(
				'LMS Enrollment',
				{'member': self.member, 'course': self.course},
				'creation',
				order_by='creation asc'
			)

		# Mark current enrollment as completed (historical record)
		self.completion_status = "Completed"
		self.access_restricted = 1
		if not self.completed_on:
			self.completed_on = now()
		self.save(ignore_permissions=True)

		# Create new enrollment record
		new_enrollment = frappe.new_doc("LMS Enrollment")
		new_enrollment.update({
			"course": self.course,
			"member": self.member,
			"member_type": self.member_type,
			"role": self.role,
			"batch_old": self.batch_old,
			"cohort": self.cohort,
			"subgroup": self.subgroup,
			"completion_status": "Re-enrolled",
			"access_restricted": 0,
			"progress": 0,
			"current_lesson": None,
			"re_enrolled_by": re_enrolled_by or frappe.session.user,
			"re_enrolled_on": now(),
			"original_enrollment_date": original_date,
			"enrollment_version": total_enrollments + 1,
			"re_enrollment_count": total_enrollments,
			"lesson_timer_data": None  # Reset timer data
		})

		# Set flag to bypass validation for re-enrollment
		new_enrollment.flags.is_re_enrollment = True
		new_enrollment.insert(ignore_permissions=True)

		# Delete all progress records for clean slate
		frappe.db.sql("""
			DELETE FROM `tabLMS Course Progress`
			WHERE member = %s AND course = %s
		""", (self.member, self.course))

		return new_enrollment

	def create_fresh_course_documents(self):
		"""Create new course documents entry for re-enrollment"""
		user_roles = frappe.get_roles(self.member)

		if "Distributor" in user_roles:
			distributor = frappe.db.get_value("Distributor", {"user_id": self.member}, "name")
			if distributor:
				# Mark previous documents as not current
				frappe.db.sql("""
					UPDATE `tabDistributor Course Documents`
					SET is_current_enrollment = 0
					WHERE distributor = %s AND course = %s
				""", (distributor, self.course))

				# Create new document record
				new_doc = frappe.new_doc("Distributor Course Documents")
				new_doc.update({
					"distributor": distributor,
					"course": self.course,
					"enrollment": self.name,
					"enrollment_version": self.enrollment_version,
					"is_current_enrollment": 1,
					"has_submitted_documents": 0,
					"submission_date": None,
					"is_certified": 0
				})
				new_doc.insert(ignore_permissions=True)

		elif "Employee" in user_roles:
			employee = frappe.db.get_value("Employee", {"user_id": self.member}, "name")
			if employee:
				# Mark previous documents as not current
				frappe.db.sql("""
					UPDATE `tabEmployee Course Documents`
					SET is_current_enrollment = 0
					WHERE employee = %s AND course = %s
				""", (employee, self.course))

				# Create new document record
				new_doc = frappe.new_doc("Employee Course Documents")
				new_doc.update({
					"employee": employee,
					"course": self.course,
					"enrollment": self.name,
					"enrollment_version": self.enrollment_version,
					"is_current_enrollment": 1,
					"submission_date": None
				})
				new_doc.insert(ignore_permissions=True)

	def get_enrollment_history(self):
		"""Get complete re-enrollment history for this user/course"""
		history = frappe.get_all(
			"LMS Enrollment",
			filters={
				"member": self.member,
				"course": self.course
			},
			fields=[
				"name", "creation", "enrollment_version", "completion_status",
				"progress", "completed_on", "re_enrolled_on", "re_enrolled_by",
				"original_enrollment_date", "re_enrollment_count"
			],
			order_by="enrollment_version asc"
		)
		return history

	def save_timer_progress(self, lesson_id, current_time, duration, completed=False):
		"""Save lesson timer progress to backend"""
		timer_data = self.lesson_timer_data or {}
		if isinstance(timer_data, str):
			try:
				import json
				timer_data = json.loads(timer_data)
			except:
				timer_data = {}

		# Update timer data for the lesson
		if lesson_id not in timer_data:
			timer_data[lesson_id] = {}

		timer_data[lesson_id].update({
			"current_time": current_time,
			"duration": duration,
			"completed": completed,
			"last_updated": now()
		})

		# Save the updated timer data
		import json
		self.lesson_timer_data = json.dumps(timer_data)
		self.save(ignore_permissions=True)

		return True

	def get_timer_progress(self, lesson_id=None):
		"""Get timer progress for lesson(s)"""
		timer_data = self.lesson_timer_data or {}
		if isinstance(timer_data, str):
			try:
				import json
				timer_data = json.loads(timer_data)
			except:
				timer_data = {}

		if lesson_id:
			return timer_data.get(lesson_id, {})
		return timer_data

	def reset_all_timers(self):
		"""Reset all lesson timer data"""
		self.lesson_timer_data = None
		self.save(ignore_permissions=True)
		return True

	def get_current_enrollment(self):
		"""Get the current (most recent) enrollment for this member/course"""
		current = frappe.get_all(
			"LMS Enrollment",
			filters={
				"member": self.member,
				"course": self.course
			},
			fields=["name", "enrollment_version", "completion_status"],
			order_by="enrollment_version desc",
			limit=1
		)
		return current[0] if current else None

	def validate_membership_in_same_batch(self):
		"""Validate that a member doesn't have duplicate active enrollments"""
		filters = {
			"member": self.member,
			"course": self.course,
			"name": ["!=", self.name]
		}
		if self.batch_old:
			filters["batch_old"] = self.batch_old

		# Check for active enrollments only (exclude completed/historical enrollments)
		# This allows re-enrollment while preventing duplicate active enrollments
		filters["completion_status"] = ["not in", ["Completed"]]

		previous_membership = frappe.db.get_value(
			"LMS Enrollment", filters, fieldname=["member_type", "member", "completion_status"], as_dict=1
		)

		if previous_membership:
			member_name = frappe.db.get_value("User", self.member, "full_name")
			course_title = frappe.db.get_value("LMS Course", self.course, "title")
			frappe.throw(
				_("{0} already has an active enrollment as {1} in the course {2}. Complete or cancel the existing enrollment before creating a new one.").format(
					member_name, previous_membership.member_type, course_title
				)
			)

	def validate_membership_in_different_batch_same_course(self):
		"""Ensures that a student is only part of one active batch."""
		# nothing to worry if the member is not a student
		if self.member_type != "Student":
			return

		course = frappe.db.get_value("LMS Batch Old", self.batch_old, "course") if self.batch_old else self.course

		# Only check for active enrollments (exclude completed ones)
		memberships = frappe.get_all(
			"LMS Enrollment",
			filters={
				"member": self.member,
				"name": ["!=", self.name],
				"member_type": "Student",
				"course": self.course,
				"completion_status": ["not in", ["Completed"]]
			},
			fields=["batch_old", "member_type", "name", "completion_status"],
		)

		if memberships:
			membership = memberships[0]
			member_name = frappe.db.get_value("User", self.member, "full_name")
			batch_name = membership.batch_old or "default"
			frappe.throw(
				_("{0} already has an active Student enrollment in {1} course through {2} batch. Complete the existing enrollment before creating a new one.").format(
					member_name, course, batch_name
				)
			)


def update_program_progress(member):
	programs = frappe.get_all("LMS Program Member", {"member": member}, ["parent", "name"])

	for program in programs:
		total_progress = 0
		courses = frappe.get_all("LMS Program Course", {"parent": program.parent}, pluck="course")
		for course in courses:
			progress = frappe.db.get_value("LMS Enrollment", {"course": course, "member": member}, "progress")
			progress = progress or 0
			total_progress += progress

		average_progress = ceil(total_progress / len(courses))
		frappe.db.set_value("LMS Program Member", program.name, "progress", average_progress)


@frappe.whitelist()
def create_membership(course, batch=None, member=None, member_type="Student", role="Member"):
	validate_course_enrollment_eligibility(course, member)

	member = member or frappe.session.user

	# Check if enrollment already exists
	existing = frappe.db.exists(
		"LMS Enrollment",
		{"course": course, "member": member}
	)

	if existing:
		# Get the most recent enrollment
		enrollment = frappe.get_all(
			"LMS Enrollment",
			filters={"course": course, "member": member},
			fields=["name"],
			order_by="enrollment_version desc",
			limit=1
		)
		return frappe.get_doc("LMS Enrollment", enrollment[0].name)

	# Create new enrollment with proper initialization
	enrollment = frappe.new_doc("LMS Enrollment")
	enrollment.update(
		{
			"doctype": "LMS Enrollment",
			"batch_old": batch,
			"course": course,
			"role": role,
			"member_type": member_type,
			"member": member,
			"completion_status": "Active",
			"access_restricted": 0,
			"enrollment_version": 1,
			"re_enrollment_count": 0,
			"original_enrollment_date": now()
		}
	)
	enrollment.insert()
	return enrollment


def validate_course_enrollment_eligibility(course, member):
	if not member:
		member = frappe.session.user

	course_details = frappe.db.get_value(
		"LMS Course",
		course,
		["published", "disable_self_learning", "paid_course", "paid_certificate"],
		as_dict=True,
	)

	if course_details.disable_self_learning:
		frappe.throw(
			_(
				"You cannot enroll in this course as self-learning is disabled. Please contact the Administrator."
			)
		)

	if not course_details.published:
		frappe.throw(_("You cannot enroll in an unpublished course."))

	if course_details.paid_course:
		payment = frappe.db.exists(
			"LMS Payment",
			{
				"reference_doctype": "LMS Course",
				"reference_docname": course,
				"member": member,
				"payment_receipt": True,
			},
		)

		if not payment:
			frappe.throw(_("You need to complete the payment for this course before enrolling."))


@frappe.whitelist()
def update_current_membership(batch, course, member):
	all_memberships = frappe.get_all("LMS Enrollment", {"member": member, "course": course})
	for membership in all_memberships:
		frappe.db.set_value("LMS Enrollment", membership.name, "is_current", 0)

	current_membership = frappe.get_all("LMS Enrollment", {"batch_old": batch, "member": member})
	if len(current_membership):
		frappe.db.set_value("LMS Enrollment", current_membership[0].name, "is_current", 1)


@frappe.whitelist()
def check_course_access(course, member=None):
	"""Check if a user can access a specific course"""
	member = member or frappe.session.user

	if frappe.session.user == "Guest":
		return {"access": False, "message": _("Please login to access courses")}

	# Get the most recent enrollment record
	current_enrollment = frappe.get_all(
		"LMS Enrollment",
		filters={"course": course, "member": member},
		fields=["name", "access_restricted", "completion_status", "progress", "enrollment_version"],
		order_by="enrollment_version desc",
		limit=1
	)

	if not current_enrollment:
		return {"access": False, "message": _("You are not enrolled in this course")}

	enrollment = current_enrollment[0]
	enrollment_doc = frappe.get_doc("LMS Enrollment", enrollment.name)

	if not enrollment_doc.can_access_course():
		return {
			"access": False,
			"message": _("Course access is restricted. You have completed this course. Please contact your admin for re-enrollment."),
			"completion_status": enrollment.completion_status,
			"completed_on": enrollment_doc.completed_on,
			"enrollment_version": enrollment.enrollment_version
		}

	return {
		"access": True,
		"enrollment": enrollment,
		"enrollment_version": enrollment.enrollment_version
	}


@frappe.whitelist()
def re_enroll_user_in_course(course, member, reset_progress=True):
	"""API endpoint to re-enroll a user in a course"""

	# Get the most recent enrollment record
	current_enrollment = frappe.get_all(
		"LMS Enrollment",
		filters={"course": course, "member": member},
		fields=["name"],
		order_by="enrollment_version desc",
		limit=1
	)

	if not current_enrollment:
		frappe.throw(_("Enrollment record not found"))

	enrollment = frappe.get_doc("LMS Enrollment", current_enrollment[0].name)

	# Create new enrollment record for re-enrollment
	new_enrollment = enrollment.re_enroll_user(frappe.session.user, reset_progress)

	if new_enrollment:
		return {
			"success": True,
			"enrollment_id": new_enrollment.name,
			"enrollment_version": new_enrollment.enrollment_version,
			"message": _("User has been successfully re-enrolled in the course. A new enrollment record has been created with progress reset to 0%.")
		}
	else:
		return {
			"success": False,
			"message": _("Failed to re-enroll user")
		}


@frappe.whitelist()
def get_user_course_enrollments(member=None, include_history=False):
	"""Get all course enrollments for a user with completion status"""
	member = member or frappe.session.user

	if include_history:
		# Return all enrollments including historical ones
		enrollments = frappe.get_all(
			"LMS Enrollment",
			filters={"member": member},
			fields=[
				"name", "course", "progress", "completion_status",
				"access_restricted", "completed_on", "re_enrolled_on",
				"member_type", "enrollment_version", "re_enrollment_count",
				"original_enrollment_date"
			],
			order_by="course, enrollment_version"
		)
	else:
		# Return only the most recent enrollment for each course
		enrollments_dict = {}
		all_enrollments = frappe.get_all(
			"LMS Enrollment",
			filters={"member": member},
			fields=[
				"name", "course", "progress", "completion_status",
				"access_restricted", "completed_on", "re_enrolled_on",
				"member_type", "enrollment_version", "re_enrollment_count",
				"original_enrollment_date"
			],
			order_by="enrollment_version desc"
		)

		# Keep only the most recent enrollment for each course
		for enrollment in all_enrollments:
			if enrollment.course not in enrollments_dict:
				enrollments_dict[enrollment.course] = enrollment

		enrollments = list(enrollments_dict.values())

	# Add course details
	for enrollment in enrollments:
		course_details = frappe.db.get_value(
			"LMS Course",
			enrollment.course,
			["title", "image", "short_introduction"],
			as_dict=True
		)
		enrollment.update(course_details)

	return enrollments


@frappe.whitelist()
def save_lesson_timer_progress(enrollment_id, lesson_id, current_time, duration, completed=False):
	"""API endpoint to save lesson timer progress"""
	enrollment = frappe.get_doc("LMS Enrollment", enrollment_id)

	# Verify the user has access to this enrollment
	if enrollment.member != frappe.session.user:
		user_roles = frappe.get_roles(frappe.session.user)
		if not any(role in ["System Manager", "Administrator", "Moderator"] for role in user_roles):
			frappe.throw(_("You don't have permission to update this enrollment"))

	success = enrollment.save_timer_progress(lesson_id, current_time, duration, completed)

	return {
		"success": success,
		"message": _("Timer progress saved successfully") if success else _("Failed to save timer progress")
	}


@frappe.whitelist()
def get_lesson_timer_progress(enrollment_id, lesson_id=None):
	"""API endpoint to get lesson timer progress"""
	enrollment = frappe.get_doc("LMS Enrollment", enrollment_id)

	# Verify the user has access to this enrollment
	if enrollment.member != frappe.session.user:
		user_roles = frappe.get_roles(frappe.session.user)
		if not any(role in ["System Manager", "Administrator", "Moderator"] for role in user_roles):
			frappe.throw(_("You don't have permission to access this enrollment"))

	timer_data = enrollment.get_timer_progress(lesson_id)

	return {
		"success": True,
		"timer_data": timer_data
	}


@frappe.whitelist()
def get_enrollment_history(course, member=None):
	"""API endpoint to get enrollment history for a user/course"""
	member = member or frappe.session.user

	# Verify access
	if member != frappe.session.user:
		user_roles = frappe.get_roles(frappe.session.user)
		if not any(role in ["System Manager", "Administrator", "Moderator"] for role in user_roles):
			frappe.throw(_("You don't have permission to view this enrollment history"))

	# Get any enrollment for this user/course to access the method
	enrollment = frappe.get_all(
		"LMS Enrollment",
		filters={"member": member, "course": course},
		fields=["name"],
		limit=1
	)

	if not enrollment:
		return {
			"success": False,
			"message": _("No enrollment found for this user and course"),
			"history": []
		}

	enrollment_doc = frappe.get_doc("LMS Enrollment", enrollment[0].name)
	history = enrollment_doc.get_enrollment_history()

	return {
		"success": True,
		"history": history
	}


@frappe.whitelist()
def get_current_enrollment(course, member=None):
	"""Get the current (most recent) enrollment for a member/course"""
	member = member or frappe.session.user

	current = frappe.get_all(
		"LMS Enrollment",
		filters={
			"member": member,
			"course": course
		},
		fields=["name", "enrollment_version", "completion_status", "progress", "access_restricted", "lesson_timer_data"],
		order_by="enrollment_version desc",
		limit=1
	)

	if current:
		return {
			"success": True,
			"enrollment": current[0]
		}
	else:
		return {
			"success": False,
			"message": _("No enrollment found for this user and course")
		}


@frappe.whitelist()
def save_lesson_timer_progress_by_course(course, lesson_id, current_time, duration, completed=False, member=None):
	"""Save lesson timer progress using course name instead of enrollment_id"""
	member = member or frappe.session.user

	# Get current enrollment
	current = frappe.get_all(
		"LMS Enrollment",
		filters={
			"member": member,
			"course": course
		},
		fields=["name"],
		order_by="enrollment_version desc",
		limit=1
	)

	if not current:
		frappe.throw(_("No enrollment found for this user and course"))

	enrollment = frappe.get_doc("LMS Enrollment", current[0].name)

	# Verify the user has access to this enrollment
	if enrollment.member != frappe.session.user:
		user_roles = frappe.get_roles(frappe.session.user)
		if not any(role in ["System Manager", "Administrator", "Moderator"] for role in user_roles):
			frappe.throw(_("You don't have permission to update this enrollment"))

	success = enrollment.save_timer_progress(lesson_id, current_time, duration, completed)

	return {
		"success": success,
		"enrollment_id": enrollment.name,
		"enrollment_version": enrollment.enrollment_version,
		"message": _("Timer progress saved successfully") if success else _("Failed to save timer progress")
	}


@frappe.whitelist()
def get_lesson_timer_progress_by_course(course, lesson_id=None, member=None):
	"""Get lesson timer progress using course name instead of enrollment_id"""
	member = member or frappe.session.user

	# Get current enrollment
	current = frappe.get_all(
		"LMS Enrollment",
		filters={
			"member": member,
			"course": course
		},
		fields=["name"],
		order_by="enrollment_version desc",
		limit=1
	)

	if not current:
		return {
			"success": False,
			"message": _("No enrollment found for this user and course"),
			"timer_data": {}
		}

	enrollment = frappe.get_doc("LMS Enrollment", current[0].name)

	# Verify the user has access to this enrollment
	if enrollment.member != frappe.session.user:
		user_roles = frappe.get_roles(frappe.session.user)
		if not any(role in ["System Manager", "Administrator", "Moderator"] for role in user_roles):
			frappe.throw(_("You don't have permission to access this enrollment"))

	timer_data = enrollment.get_timer_progress(lesson_id)

	return {
		"success": True,
		"enrollment_id": enrollment.name,
		"enrollment_version": enrollment.enrollment_version,
		"timer_data": timer_data
	}


# Migration function to update existing enrollments
def migrate_existing_enrollments():
	"""Update existing enrollments with new versioning fields"""
	enrollments = frappe.get_all("LMS Enrollment", fields=["name", "progress", "member", "course", "creation"])

	# Group enrollments by member and course
	enrollments_by_user_course = {}
	for enrollment in enrollments:
		key = f"{enrollment.member}:{enrollment.course}"
		if key not in enrollments_by_user_course:
			enrollments_by_user_course[key] = []
		enrollments_by_user_course[key].append(enrollment)

	# Sort and update each group
	for key, group in enrollments_by_user_course.items():
		# Sort by creation date
		group.sort(key=lambda x: x.creation)

		for idx, enrollment in enumerate(group):
			doc = frappe.get_doc("LMS Enrollment", enrollment.name)

			# Set enrollment version
			if not doc.enrollment_version:
				doc.enrollment_version = idx + 1

			# Set original enrollment date
			if not doc.original_enrollment_date:
				doc.original_enrollment_date = group[0].creation

			# Set re-enrollment count
			if not doc.re_enrollment_count:
				doc.re_enrollment_count = idx

			# Set default values for completion status
			if not doc.completion_status:
				if doc.progress and flt(doc.progress) >= 100.0:
					doc.completion_status = "Completed"
					doc.access_restricted = 1
					if not doc.completed_on:
						doc.completed_on = doc.modified
				else:
					doc.completion_status = "Active"
					doc.access_restricted = 0

			doc.save(ignore_permissions=True)

	# Update course documents to link with enrollments
	migrate_course_documents()

	frappe.db.commit()
	print(f"Updated {len(enrollments)} enrollment records")

def migrate_course_documents():
	"""Update existing course documents with enrollment links and versioning"""
	# Update Distributor Course Documents
	dist_docs = frappe.get_all(
		"Distributor Course Documents",
		fields=["name", "distributor", "course"]
	)

	for doc_data in dist_docs:
		doc = frappe.get_doc("Distributor Course Documents", doc_data.name)

		# Find the distributor's user
		user_id = frappe.db.get_value("Distributor", doc.distributor, "user_id")
		if user_id:
			# Find the most recent enrollment
			enrollment = frappe.get_all(
				"LMS Enrollment",
				filters={"member": user_id, "course": doc.course},
				fields=["name", "enrollment_version"],
				order_by="enrollment_version desc",
				limit=1
			)

			if enrollment:
				if not doc.get("enrollment"):
					doc.enrollment = enrollment[0].name
				if not doc.get("enrollment_version"):
					doc.enrollment_version = enrollment[0].enrollment_version
				if not doc.get("is_current_enrollment"):
					doc.is_current_enrollment = 1
				doc.save(ignore_permissions=True)

	# Update Employee Course Documents
	emp_docs = frappe.get_all(
		"Employee Course Documents",
		fields=["name", "employee", "course"]
	)

	for doc_data in emp_docs:
		doc = frappe.get_doc("Employee Course Documents", doc_data.name)

		# Find the employee's user
		user_id = frappe.db.get_value("Employee", doc.employee, "user_id")
		if user_id:
			# Find the most recent enrollment
			enrollment = frappe.get_all(
				"LMS Enrollment",
				filters={"member": user_id, "course": doc.course},
				fields=["name", "enrollment_version"],
				order_by="enrollment_version desc",
				limit=1
			)

			if enrollment:
				if not doc.get("enrollment"):
					doc.enrollment = enrollment[0].name
				if not doc.get("enrollment_version"):
					doc.enrollment_version = enrollment[0].enrollment_version
				if not doc.get("is_current_enrollment"):
					doc.is_current_enrollment = 1
				doc.save(ignore_permissions=True)

	print(f"Updated {len(dist_docs)} distributor and {len(emp_docs)} employee course documents")

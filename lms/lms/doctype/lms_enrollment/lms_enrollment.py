# Copyright (c) 2021, FOSS United and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import ceil, now, flt


class LMSEnrollment(Document):
	def validate(self):
		self.validate_membership_in_same_batch()
		self.validate_membership_in_different_batch_same_course()

	def on_update(self):
		self.update_program_progress()
		self.check_course_completion()

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
		admin_roles = ["System Manager", "Administrator", "Moderator"]
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

	def re_enroll_user(self, re_enrolled_by=None, reset_progress=False):
		"""Re-enroll user and restore course access"""
		if not self.can_re_enroll(re_enrolled_by):
			frappe.throw(_("You don't have permission to re-enroll this user"))
			
		self.completion_status = "Re-enrolled"
		self.access_restricted = 0
		self.re_enrolled_by = re_enrolled_by or frappe.session.user
		self.re_enrolled_on = now()
		
		if reset_progress:
			self.progress = 0
			self.current_lesson = None
			
			# Delete all existing lesson progress records for this enrollment
			# This ensures fresh tracking for the new enrollment cycle
			frappe.db.sql("""
				DELETE FROM `tabLMS Course Progress`
				WHERE enrollment = %s
			""", self.name)
			
			# Also delete any orphaned progress records for this member and course
			# that might not have enrollment links (legacy data)
			frappe.db.sql("""
				DELETE FROM `tabLMS Course Progress`
				WHERE member = %s 
				AND course = %s
				AND (enrollment IS NULL OR enrollment = '')
			""", (self.member, self.course))
			
		else:
			# If not resetting progress, just update existing records to link to this enrollment
			frappe.db.sql("""
				UPDATE `tabLMS Course Progress`
				SET enrollment = %s
				WHERE member = %s 
				AND course = %s
				AND (enrollment IS NULL OR enrollment = '')
			""", (self.name, self.member, self.course))
			
		self.save()
		
		frappe.logger().info(f"User {self.member} re-enrolled in course {self.course} by {self.re_enrolled_by}")
		
		return True

	def can_re_enroll(self, user=None):
		"""Check if the given user can re-enroll this enrollment"""
		user = user or frappe.session.user
		user_roles = frappe.get_roles(user)
		
		# System Manager and Administrator can always re-enroll
		if "System Manager" in user_roles or "Administrator" in user_roles:
			return True
			
		# Moderators can re-enroll distributors and employees
		if "Moderator" in user_roles:
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

	def validate_membership_in_same_batch(self):
		filters = {"member": self.member, "course": self.course, "name": ["!=", self.name]}
		if self.batch_old:
			filters["batch_old"] = self.batch_old
		previous_membership = frappe.db.get_value(
			"LMS Enrollment", filters, fieldname=["member_type", "member"], as_dict=1
		)

		if previous_membership:
			member_name = frappe.db.get_value("User", self.member, "full_name")
			course_title = frappe.db.get_value("LMS Course", self.course, "title")
			frappe.throw(
				_("{0} is already a {1} of the course {2}").format(
					member_name, previous_membership.member_type, course_title
				)
			)

	def validate_membership_in_different_batch_same_course(self):
		"""Ensures that a studnet is only part of one batch."""
		# nothing to worry if the member is not a student
		if self.member_type != "Student":
			return

		course = frappe.db.get_value("LMS Batch Old", self.batch_old, "course")
		memberships = frappe.get_all(
			"LMS Enrollment",
			filters={
				"member": self.member,
				"name": ["!=", self.name],
				"member_type": "Student",
				"course": self.course,
			},
			fields=["batch_old", "member_type", "name"],
		)

		if memberships:
			membership = memberships[0]
			member_name = frappe.db.get_value("User", self.member, "full_name")
			frappe.throw(
				_("{0} is already a Student of {1} course through {2} batch").format(
					member_name, course, membership.batch_old
				)
			)

	def update_program_progress(self):
		programs = frappe.get_all(
			"LMS Program Member", {"member": self.member}, ["parent", "name"]
		)

		for program in programs:
			total_progress = 0
			courses = frappe.get_all(
				"LMS Program Course", {"parent": program.parent}, pluck="course"
			)
			for course in courses:
				progress = frappe.db.get_value(
					"LMS Enrollment", {"course": course, "member": self.member}, "progress"
				)
				progress = progress or 0
				total_progress += progress

			average_progress = ceil(total_progress / len(courses))
			frappe.db.set_value("LMS Program Member", program.name, "progress", average_progress)


@frappe.whitelist()
def create_membership(
	course, batch=None, member=None, member_type="Student", role="Member"
):
	if frappe.db.get_value("LMS Course", course, "disable_self_learning"):
		return False

	enrollment = frappe.new_doc("LMS Enrollment")
	enrollment.update(
		{
			"doctype": "LMS Enrollment",
			"batch_old": batch,
			"course": course,
			"role": role,
			"member_type": member_type,
			"member": member or frappe.session.user,
			"completion_status": "Active",
			"access_restricted": 0
		}
	)
	enrollment.insert()
	return enrollment


@frappe.whitelist()
def update_current_membership(batch, course, member):
	all_memberships = frappe.get_all(
		"LMS Enrollment", {"member": member, "course": course}
	)
	for membership in all_memberships:
		frappe.db.set_value("LMS Enrollment", membership.name, "is_current", 0)

	current_membership = frappe.get_all(
		"LMS Enrollment", {"batch_old": batch, "member": member}
	)
	if len(current_membership):
		frappe.db.set_value("LMS Enrollment", current_membership[0].name, "is_current", 1)


@frappe.whitelist()
def check_course_access(course, member=None):
	"""Check if a user can access a specific course"""
	member = member or frappe.session.user
	
	if frappe.session.user == "Guest":
		return {"access": False, "message": _("Please login to access courses")}
	
	# Get enrollment record
	enrollment = frappe.db.get_value(
		"LMS Enrollment",
		{"course": course, "member": member},
		["name", "access_restricted", "completion_status", "progress"],
		as_dict=True
	)
	
	if not enrollment:
		return {"access": False, "message": _("You are not enrolled in this course")}
	
	enrollment_doc = frappe.get_doc("LMS Enrollment", enrollment.name)
	
	if not enrollment_doc.can_access_course():
		return {
			"access": False, 
			"message": _("Course access is restricted. You have completed this course. Please contact your admin for re-enrollment."),
			"completion_status": enrollment.completion_status,
			"completed_on": frappe.db.get_value("LMS Enrollment", enrollment.name, "completed_on")
		}
	
	return {"access": True, "enrollment": enrollment}


@frappe.whitelist()
def re_enroll_user_in_course(course, member, reset_progress=False):
	"""API endpoint to re-enroll a user in a course"""
	
	# Get enrollment record
	enrollment = frappe.get_doc("LMS Enrollment", {"course": course, "member": member})
	
	if not enrollment:
		frappe.throw(_("Enrollment record not found"))
	
	success = enrollment.re_enroll_user(frappe.session.user, reset_progress)
	
	if success:
		return {
			"success": True,
			"message": _("User has been successfully re-enrolled in the course")
		}
	else:
		return {
			"success": False,
			"message": _("Failed to re-enroll user")
		}


@frappe.whitelist()
def get_user_course_enrollments(member=None):
	"""Get all course enrollments for a user with completion status"""
	member = member or frappe.session.user
	
	enrollments = frappe.get_all(
		"LMS Enrollment",
		filters={"member": member},
		fields=[
			"name", "course", "progress", "completion_status", 
			"access_restricted", "completed_on", "re_enrolled_on", "member_type"
		]
	)
	
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


# Migration function to update existing enrollments
def migrate_existing_enrollments():
	"""Update existing enrollments with new completion status fields"""
	enrollments = frappe.get_all("LMS Enrollment", fields=["name", "progress", "member"])
	
	for enrollment in enrollments:
		doc = frappe.get_doc("LMS Enrollment", enrollment.name)
		
		# Set default values for new fields
		if not doc.completion_status:
			if doc.progress and flt(doc.progress) >= 100.0:
				doc.completion_status = "Completed"
				doc.access_restricted = 1
				doc.completed_on = doc.modified  # Use last modified as completion date
			else:
				doc.completion_status = "Active"
				doc.access_restricted = 0
		
		doc.save()
	
	frappe.db.commit()
	print(f"Updated {len(enrollments)} enrollment records")

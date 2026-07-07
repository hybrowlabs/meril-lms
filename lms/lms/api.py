from __future__ import annotations
import frappe



@frappe.whitelist(allow_guest=False)
def can_re_enroll_user(member_email: str | None = None, course_name: str | None = None):
    """
    Check if a user can be re-enrolled in a course.
    Blocks if the latest enrollment is Active/Re-enrolled and progress < 100.

    Returns:
        { "can_re_enroll": bool, "reason": str | None }
    """
    if not member_email or not course_name:
        return {"can_re_enroll": False, "reason": "missing_params"}

    latest = frappe.db.get_value(
        "LMS Enrollment",
        {"member": member_email, "course": course_name},
        ["name", "progress", "completion_status", "enrollment_version"],
        as_dict=True,
        order_by="enrollment_version desc",
    )

    if not latest:
        # No enrollment yet; allow re-enroll call to create one per your flow
        return {"can_re_enroll": True}

    status = (latest.get("completion_status") or "").strip()
    try:
        progress = float(latest.get("progress") or 0)
    except Exception:
        progress = 0.0

    if status in {"Re-enrolled", "Active"} and progress < 100.0:
        return {"can_re_enroll": False, "reason": "already_running"}

    return {"can_re_enroll": True}

"""API methods for the LMS.
"""

import json
import frappe
import zipfile
import os
import re
import shutil
import xml.etree.ElementTree as ET
from frappe.translate import get_all_translations
from frappe import _
from frappe.utils import (
	get_datetime,
	cint,
	flt,
	now,
	add_days,
	format_date,
	date_diff,
)
from frappe.query_builder import DocType
from lms.lms.utils import get_average_rating, get_lesson_count
from xml.dom.minidom import parseString
from lms.lms.doctype.course_lesson.course_lesson import save_progress
from frappe.integrations.frappe_providers.frappecloud_billing import (
	is_fc_site,
	current_site_info,
)
from frappe.utils.print_format import download_pdf
from frappe.exceptions import PermissionError
import mimetypes

@frappe.whitelist()
def distributor_download_pdf(doctype, name, format=None, no_letterhead=0, letterhead=None, settings=None):
	user = frappe.session.user

	roles = frappe.get_roles(user)

	if ("System Manager" in roles) or ("Administrator" in roles) or ("Supervisor" in roles):
		return download_pdf(doctype, name, format, no_letterhead=no_letterhead, letterhead=letterhead)

	# Only check linked permission for specific doctypes
	if doctype == "Employee Course Documents":
		employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
		linked_employee = frappe.db.get_value(doctype, name, "employee")
		if not (employee and linked_employee == employee):
			raise PermissionError(_("You are not allowed to download this PDF"))
	elif doctype == "Distributor Course Documents":
		distributor = frappe.db.get_value("Distributor", {"user_id": user}, "name")
		linked_distributor = frappe.db.get_value(doctype, name, "distributor")
		if not (distributor and linked_distributor == distributor):
			raise PermissionError(_("You are not allowed to download this PDF"))

	return download_pdf(doctype, name, format, no_letterhead=no_letterhead, letterhead=letterhead)

@frappe.whitelist()
def autosave_section(section, code):
	"""Saves the code edited in one of the sections."""
	doc = frappe.get_doc(
		doctype="Code Revision", section=section, code=code, author=frappe.session.user
	)
	doc.insert()
	return {"name": doc.name}


@frappe.whitelist()
def submit_solution(exercise, code):
	"""Submits a solution.

	@exerecise: name of the exercise to submit
	@code: solution to the exercise
	"""
	ex = frappe.get_doc("LMS Exercise", exercise)
	if not ex:
		return
	doc = ex.submit(code)
	return {"name": doc.name, "creation": doc.creation}


@frappe.whitelist()
def save_current_lesson(course_name, lesson_name):
	"""Saves the current lesson for a student/mentor."""
	name = frappe.get_value(
		doctype="LMS Enrollment",
		filters={"course": course_name, "member": frappe.session.user},
		fieldname="name",
	)
	if not name:
		return
	frappe.db.set_value("LMS Enrollment", name, "current_lesson", lesson_name)


@frappe.whitelist()
def join_cohort(course, cohort, subgroup, invite_code):
	"""Creates a Cohort Join Request for given user."""
	course_doc = frappe.get_doc("LMS Course", course)
	cohort_doc = course_doc and course_doc.get_cohort(cohort)
	subgroup_doc = cohort_doc and subgroup_doc.get_subgroup(subgroup)

	if not subgroup_doc or subgroup_doc.invite_code != invite_code:
		return {"ok": False, "error": "Invalid join link"}

	data = {
		"doctype": "Cohort Join Request",
		"cohort": cohort_doc.name,
		"subgroup": subgroup_doc.name,
		"email": frappe.session.user,
		"status": "Pending",
	}
	# Don't insert duplicate records
	if frappe.db.exists(data):
		return {"ok": True, "status": "record found"}
	else:
		doc = frappe.get_doc(data)
		doc.insert()
		return {"ok": True, "status": "record created"}


@frappe.whitelist()
def approve_cohort_join_request(join_request):
	r = frappe.get_doc("Cohort Join Request", join_request)
	sg = r and frappe.get_doc("Cohort Subgroup", r.subgroup)
	if not sg or r.status not in ["Pending", "Accepted"]:
		return {"ok": False, "error": "Invalid Join Request"}
	if (
		not sg.is_manager(frappe.session.user) and "System Manager" not in frappe.get_roles()
	):
		return {"ok": False, "error": "Permission Deined"}

	r.status = "Accepted"
	r.save()
	return {"ok": True}


@frappe.whitelist()
def reject_cohort_join_request(join_request):
	r = frappe.get_doc("Cohort Join Request", join_request)
	sg = r and frappe.get_doc("Cohort Subgroup", r.subgroup)
	if not sg or r.status not in ["Pending", "Rejected"]:
		return {"ok": False, "error": "Invalid Join Request"}
	if (
		not sg.is_manager(frappe.session.user) and "System Manager" not in frappe.get_roles()
	):
		return {"ok": False, "error": "Permission Deined"}

	r.status = "Rejected"
	r.save()
	return {"ok": True}


@frappe.whitelist()
def undo_reject_cohort_join_request(join_request):
	r = frappe.get_doc("Cohort Join Request", join_request)
	sg = r and frappe.get_doc("Cohort Subgroup", r.subgroup)
	# keeping Pending as well to consider the case of duplicate requests
	if not sg or r.status not in ["Pending", "Rejected"]:
		return {"ok": False, "error": "Invalid Join Request"}
	if (
		not sg.is_manager(frappe.session.user) and "System Manager" not in frappe.get_roles()
	):
		return {"ok": False, "error": "Permission Deined"}

	r.status = "Pending"
	r.save()
	return {"ok": True}


@frappe.whitelist()
def add_mentor_to_subgroup(subgroup, email):
	try:
		sg = frappe.get_doc("Cohort Subgroup", subgroup)
	except frappe.DoesNotExistError:
		return {"ok": False, "error": f"Invalid subgroup: {subgroup}"}

	if (
		not sg.get_cohort().is_admin(frappe.session.user)
		and "System Manager" not in frappe.get_roles()
	):
		return {"ok": False, "error": "Permission Deined"}

	try:
		user = frappe.get_doc("User", email)
	except frappe.DoesNotExistError:
		return {"ok": False, "error": f"Invalid user: {email}"}

	sg.add_mentor(email)
	return {"ok": True}


@frappe.whitelist(allow_guest=True)
def get_user_info():
	if frappe.session.user == "Guest":
		return None

	user = frappe.db.get_value(
		"User",
		frappe.session.user,
		["name", "email", "enabled", "user_image", "full_name", "user_type", "username"],
		as_dict=1,
	)
	user["roles"] = frappe.get_roles(user.name)
	user.is_instructor = "Course Creator" in user.roles
	user.is_moderator = "Moderator" in user.roles
	user.is_evaluator = "Batch Evaluator" in user.roles
	user.is_student = (
		not user.is_instructor and not user.is_moderator and not user.is_evaluator
	)
	user.is_fc_site = is_fc_site()
	user.is_system_manager = "System Manager" in user.roles
	user.sitename = frappe.local.site
	user.developer_mode = frappe.conf.developer_mode
	if user.is_fc_site and user.is_system_manager:
		user.site_info = current_site_info()
	return user


@frappe.whitelist(allow_guest=True)
def get_translations():
	if frappe.session.user != "Guest":
		language = frappe.db.get_value("User", frappe.session.user, "language")
	else:
		language = frappe.db.get_single_value("System Settings", "language")
	return get_all_translations(language)


@frappe.whitelist()
def validate_billing_access(billing_type, name):
	access = True
	message = ""
	doctype = "LMS Batch" if billing_type == "batch" else "LMS Course"

	if frappe.session.user == "Guest":
		access = False
		message = _("Please login to continue with payment.")

	if access and billing_type not in ["course", "batch", "certificate"]:
		access = False
		message = _("Module is incorrect.")

	if access and not frappe.db.exists(doctype, name):
		access = False
		message = _("Module Name is incorrect or does not exist.")

	if access and billing_type == "course":
		membership = frappe.db.exists(
			"LMS Enrollment", {"member": frappe.session.user, "course": name}
		)
		if membership:
			access = False
			message = _("You are already enrolled for this course.")

	elif access and billing_type == "batch":
		membership = frappe.db.exists(
			"LMS Batch Enrollment", {"member": frappe.session.user, "batch": name}
		)
		if membership:
			access = False
			message = _("You are already enrolled for this batch.")

		seat_count = frappe.get_cached_value("LMS Batch", name, "seat_count")
		number_of_students = frappe.db.count("LMS Batch Enrollment", {"batch": name})
		if seat_count <= number_of_students:
			access = False
			message = _("Batch is sold out.")

		start_date = frappe.get_cached_value("LMS Batch", name, "start_date")
		if start_date and date_diff(start_date, now()) < 0:
			access = False
			message = _("Batch has already started.")

	elif access and billing_type == "certificate":
		purchased_certificate = frappe.db.exists(
			"LMS Enrollment",
			{
				"course": name,
				"member": frappe.session.user,
				"purchased_certificate": 1,
			},
		)
		if purchased_certificate:
			access = False
			message = _("You have already purchased the certificate for this course.")

	address = frappe.db.get_value(
		"Address",
		{"email_id": frappe.session.user},
		[
			"name",
			"address_title as billing_name",
			"address_line1",
			"address_line2",
			"city",
			"state",
			"country",
			"pincode",
			"phone",
		],
		as_dict=1,
	)

	return {"access": access, "message": message, "address": address}


@frappe.whitelist(allow_guest=True)
def get_job_details(job):
	return frappe.db.get_value(
		"Job Opportunity",
		job,
		[
			"job_title",
			"location",
			"country",
			"type",
			"company_name",
			"company_logo",
			"company_website",
			"name",
			"creation",
			"description",
			"owner",
		],
		as_dict=1,
	)


@frappe.whitelist(allow_guest=True)
def get_job_opportunities(filters=None, orFilters=None):
	if not filters:
		filters = {}

	jobs = frappe.get_all(
		"Job Opportunity",
		filters=filters,
		or_filters=orFilters,
		fields=[
			"job_title",
			"location",
			"country",
			"type",
			"company_name",
			"company_logo",
			"name",
			"creation",
			"description",
		],
		order_by="creation desc",
	)

	for job in jobs:
		job.description = frappe.utils.strip_html_tags(job.description)
		job.applicants = frappe.db.count("LMS Job Application", {"job": job.name})
	return jobs


@frappe.whitelist(allow_guest=True)
def get_chart_details():
	details = frappe._dict()
	details.enrollments = frappe.db.count("LMS Enrollment")
	details.courses = frappe.db.count(
		"LMS Course",
		{
			"published": 1,
			"upcoming": 0,
		},
	)
	details.users = frappe.db.count(
		"User", {"enabled": 1, "name": ["not in", ("Administrator", "Guest")]}
	)
	details.completions = frappe.db.count(
		"LMS Enrollment", {"progress": ["like", "%100%"]}
	)
	details.certifications = frappe.db.count("LMS Certificate", {"published": 1})
	return details


@frappe.whitelist()
def get_file_info(file_url):
	"""Get file info for the given file URL."""
	file_info = frappe.db.get_value(
		"File", {"file_url": file_url}, ["file_name", "file_size", "file_url"], as_dict=1
	)
	return file_info


@frappe.whitelist(allow_guest=True)
def get_branding():
	"""Get branding details."""
	website_settings = frappe.get_single("Website Settings")
	image_fields = ["banner_image", "footer_logo", "favicon"]

	for field in image_fields:
		if website_settings.get(field):
			file_info = get_file_info(website_settings.get(field))
			website_settings.update({field: json.loads(json.dumps(file_info))})
		else:
			website_settings.update({field: None})

	return website_settings


@frappe.whitelist()
def get_unsplash_photos(keyword=None):
	from lms.unsplash import get_list, get_by_keyword

	if keyword:
		return get_by_keyword(keyword)

	return frappe.cache().get_value("unsplash_photos", generator=get_list)


@frappe.whitelist()
def get_evaluator_details(evaluator):
	frappe.only_for("Batch Evaluator")

	if not frappe.db.exists("Google Calendar", {"user": evaluator}):
		calendar = frappe.new_doc("Google Calendar")
		calendar.update({"user": evaluator, "calendar_name": evaluator})
		calendar.insert()
	else:
		calendar = frappe.db.get_value(
			"Google Calendar", {"user": evaluator}, ["name", "authorization_code"], as_dict=1
		)

	if frappe.db.exists("Course Evaluator", {"evaluator": evaluator}):
		doc = frappe.get_doc("Course Evaluator", evaluator)
	else:
		doc = frappe.new_doc("Course Evaluator")
		doc.evaluator = evaluator
		doc.insert()

	return {
		"slots": doc.as_dict(),
		"calendar": calendar.name,
		"is_authorised": calendar.authorization_code,
	}


@frappe.whitelist(allow_guest=True)
def get_certified_participants(filters=None, start=0, page_length=100):
	or_filters = {}
	if not filters:
		filters = {}

	filters.update({"published": 1})

	category = filters.get("category")
	if category:
		del filters["category"]
		or_filters["course_title"] = ["like", f"%{category}%"]
		or_filters["batch_title"] = ["like", f"%{category}%"]

	participants = frappe.db.get_all(
		"LMS Certificate",
		filters=filters,
		or_filters=or_filters,
		fields=["member", "issue_date"],
		group_by="member",
		order_by="issue_date desc",
		start=start,
		page_length=page_length,
	)

	for participant in participants:
		count = frappe.db.count("LMS Certificate", {"member": participant.member})
		details = frappe.db.get_value(
			"User",
			participant.member,
			["full_name", "user_image", "username", "country", "headline"],
			as_dict=1,
		)
		details["certificate_count"] = count
		participant.update(details)

	return participants


@frappe.whitelist(allow_guest=True)
def get_count_of_certified_members(filters=None):
	Certificate = DocType("LMS Certificate")

	query = (
		frappe.qb.from_(Certificate)
		.select(Certificate.member)
		.distinct()
		.where(Certificate.published == 1)
	)

	if filters:
		for field, value in filters.items():
			if field == "category":
				query = query.where(
					Certificate.course_title.like(f"%{value}%")
					| Certificate.batch_title.like(f"%{value}%")
				)
			elif field == "member_name":
				query = query.where(Certificate.member_name.like(value[1]))

	result = query.run(as_dict=True)
	return len(result) or 0


@frappe.whitelist(allow_guest=True)
def get_certification_categories():
	categories = []
	docs = frappe.get_all(
		"LMS Certificate",
		filters={
			"published": 1,
		},
		fields=["course_title", "batch_title"],
	)

	for doc in docs:
		category = doc.course_title if doc.course_title else doc.batch_title
		if category not in categories:
			categories.append(category)

	return categories


@frappe.whitelist()
def get_assigned_badges(member):
	assigned_badges = frappe.get_all(
		"LMS Badge Assignment",
		{"member": member},
		["badge"],
		as_dict=1,
	)

	for badge in assigned_badges:
		badge.update(
			frappe.db.get_value("LMS Badge", badge.badge, ["name", "title", "image"])
		)
	return assigned_badges


@frappe.whitelist()
def get_all_users():
	frappe.only_for(["Moderator", "Course Creator", "Batch Evaluator"])
	users = frappe.get_all(
		"User",
		{
			"enabled": 1,
		},
		["name", "full_name", "user_image"],
	)

	return {user.name: user for user in users}


@frappe.whitelist()
def mark_as_read(name):
	doc = frappe.get_doc("Notification Log", name)
	doc.read = 1
	doc.save(ignore_permissions=True)


@frappe.whitelist()
def mark_all_as_read():
	notifications = frappe.get_all(
		"Notification Log", {"for_user": frappe.session.user, "read": 0}, pluck="name"
	)

	for notification in notifications:
		mark_as_read(notification)


@frappe.whitelist(allow_guest=True)
def get_sidebar_settings():
	lms_settings = frappe.get_single("LMS Settings")
	sidebar_items = frappe._dict()

	items = [
		"courses",
		"batches",
		"certified_members",
		"jobs",
		"statistics",
		"notifications",
	]
	for item in items:
		sidebar_items[item] = lms_settings.get(item)

	if len(lms_settings.sidebar_items):
		web_pages = frappe.get_all(
			"LMS Sidebar Item",
			{"parenttype": "LMS Settings", "parentfield": "sidebar_items"},
			["web_page", "route", "title as label", "icon"],
		)
		for page in web_pages:
			page.to = page.route

		sidebar_items.web_pages = web_pages

	return sidebar_items


@frappe.whitelist()
def update_sidebar_item(webpage, icon):
	filters = {
		"web_page": webpage,
		"parenttype": "LMS Settings",
		"parentfield": "sidebar_items",
		"parent": "LMS Settings",
	}

	if frappe.db.exists("LMS Sidebar Item", filters):
		frappe.db.set_value("LMS Sidebar Item", filters, "icon", icon)
	else:
		doc = frappe.new_doc("LMS Sidebar Item")
		doc.update(filters)
		doc.icon = icon
		doc.insert()


@frappe.whitelist()
def delete_sidebar_item(webpage):
	return frappe.db.delete(
		"LMS Sidebar Item",
		{
			"web_page": webpage,
			"parenttype": "LMS Settings",
			"parentfield": "sidebar_items",
			"parent": "LMS Settings",
		},
	)


@frappe.whitelist()
def delete_lesson(lesson, chapter):
	# Delete Reference
	chapter = frappe.get_doc("Course Chapter", chapter)
	chapter.lessons = [row for row in chapter.lessons if row.lesson != lesson]
	chapter.save()

	# Delete progress
	frappe.db.delete("LMS Course Progress", {"lesson": lesson})

	# Delete Lesson
	frappe.db.delete("Course Lesson", lesson)


@frappe.whitelist()
def update_lesson_index(lesson, sourceChapter, targetChapter, idx):
	hasMoved = sourceChapter == targetChapter

	update_source_chapter(lesson, sourceChapter, idx, hasMoved)
	if not hasMoved:
		update_target_chapter(lesson, targetChapter, idx)


def update_source_chapter(lesson, chapter, idx, hasMoved=False):
	lessons = frappe.get_all(
		"Lesson Reference",
		{
			"parent": chapter,
		},
		pluck="lesson",
		order_by="idx",
	)

	lessons.remove(lesson)
	if not hasMoved:
		frappe.db.delete("Lesson Reference", {"parent": chapter, "lesson": lesson})
	else:
		lessons.insert(idx, lesson)

	update_index(lessons, chapter)


def update_target_chapter(lesson, chapter, idx):
	lessons = frappe.get_all(
		"Lesson Reference",
		{
			"parent": chapter,
		},
		pluck="lesson",
		order_by="idx",
	)

	lessons.insert(idx, lesson)
	new_lesson_reference = frappe.new_doc("Lesson Reference")
	new_lesson_reference.update(
		{
			"lesson": lesson,
			"parent": chapter,
			"parenttype": "Course Chapter",
			"parentfield": "lessons",
		}
	)
	new_lesson_reference.insert()
	update_index(lessons, chapter)


def update_index(lessons, chapter):
	for row in lessons:
		frappe.db.set_value(
			"Lesson Reference", {"lesson": row, "parent": chapter}, "idx", lessons.index(row) + 1
		)


@frappe.whitelist(allow_guest=True)
def get_categories(doctype, filters):
	categoryOptions = []

	categories = frappe.get_all(
		doctype,
		filters,
		pluck="category",
	)
	categories = list(set(categories))

	for category in categories:
		if category:
			categoryOptions.append({"label": category, "value": category})

	return categoryOptions


@frappe.whitelist()
def get_members(start=0, search=""):
	"""Get members for the given search term and start index.
	                                                                Args: start (int): Start index for the query.
	<<<<<<< HEAD
	                                                                search (str): Search term to filter the results.
	=======
	                                                                                                                                                                                                                                                                                                                                search (str): Search term to filter the results.
	>>>>>>> 4869bba7bbb2fb38477d6fc29fb3b5838e075577
	                                                                Returns: List of members.
	"""

	filters = {"enabled": 1, "name": ["not in", ["Administrator", "Guest"]]}
	or_filters = {}

	if search:
		or_filters["full_name"] = ["like", f"%{search}%"]
		or_filters["email"] = ["like", f"%{search}%"]

	members = frappe.get_all(
		"User",
		filters=filters,
		fields=["name", "full_name", "user_image", "username", "last_active"],
		or_filters=or_filters,
		page_length=20,
		start=start,
	)

	for member in members:
		roles = frappe.get_roles(member.name)
		if "Moderator" in roles:
			member.role = "Moderator"
		elif "Course Creator" in roles:
			member.role = "Course Creator"
		elif "Batch Evaluator" in roles:
			member.role = "Batch Evaluator"
		elif "LMS Student" in roles:
			member.role = "LMS Student"

	return members


def check_app_permission():
	"""Check if the user has permission to access the app."""
	if frappe.session.user == "Administrator":
		return True

	roles = frappe.get_roles()
	lms_roles = ["Moderator", "Course Creator", "Batch Evaluator", "LMS Student", "Distributor"]
	if any(role in roles for role in lms_roles):
		return True

	return False


@frappe.whitelist()
def save_evaluation_details(
	member,
	course,
	batch_name,
	evaluator,
	date,
	start_time,
	end_time,
	status,
	rating,
	summary,
):
	"""
	Save evaluation details for a member against a course.
	"""
	evaluation = frappe.db.exists(
		"LMS Certificate Evaluation", {"member": member, "course": course}
	)

	details = {
		"date": date,
		"start_time": start_time,
		"end_time": end_time,
		"status": status,
		"rating": rating / 5,
		"summary": summary,
		"batch_name": batch_name,
	}

	if evaluation:
		frappe.db.set_value("LMS Certificate Evaluation", evaluation, details)
		return evaluation
	else:
		doc = frappe.new_doc("LMS Certificate Evaluation")
		details.update(
			{
				"member": member,
				"course": course,
				"evaluator": evaluator,
			}
		)
		doc.update(details)
		doc.insert()
		return doc.name


@frappe.whitelist()
def save_certificate_details(
	member,
	course,
	batch_name,
	evaluator,
	issue_date,
	expiry_date,
	template,
	published=True,
):
	"""
	Save certificate details for a member against a course.
	"""
	certificate = frappe.db.exists("LMS Certificate", {"member": member, "course": course})

	details = {
		"published": published,
		"issue_date": issue_date,
		"expiry_date": expiry_date,
		"template": template,
		"batch_name": batch_name,
	}

	if certificate:
		frappe.db.set_value("LMS Certificate", certificate, details)
		return certificate
	else:
		doc = frappe.new_doc("LMS Certificate")
		details.update(
			{
				"member": member,
				"course": course,
				"evaluator": evaluator,
			}
		)
		doc.update(details)
		doc.insert()
		return doc.name


@frappe.whitelist()
def delete_documents(doctype, documents):
	frappe.only_for("Moderator")
	for doc in documents:
		frappe.delete_doc(doctype, doc)


@frappe.whitelist(allow_guest=True)
def get_count(doctype, filters):
	return frappe.db.count(
		doctype,
		filters=filters,
	)


@frappe.whitelist()
def get_payment_gateway_details(payment_gateway):
	fields = []
	gateway = frappe.get_doc("Payment Gateway", payment_gateway)

	if gateway.gateway_controller is None:
		try:
			data = frappe.get_doc(f"{payment_gateway} Settings").as_dict()
			meta = frappe.get_meta(f"{payment_gateway} Settings").fields
			doctype = f"{payment_gateway} Settings"
			docname = f"{payment_gateway} Settings"
		except Exception:
			frappe.throw(_("{0} Settings not found").format(payment_gateway))
	else:
		try:
			data = frappe.get_doc(gateway.gateway_settings, gateway.gateway_controller).as_dict()
			meta = frappe.get_meta(gateway.gateway_settings).fields
			doctype = gateway.gateway_settings
			docname = gateway.gateway_controller
		except Exception:
			frappe.throw(_("{0} Settings not found").format(payment_gateway))

	for row in meta:
		if row.fieldtype not in ["Column Break", "Section Break"]:
			if row.fieldtype in ["Attach", "Attach Image"]:
				fieldtype = "Upload"
				data[row.fieldname] = get_file_info(data.get(row.fieldname))
			else:
				fieldtype = row.fieldtype

			fields.append(
				{
					"label": row.label,
					"name": row.fieldname,
					"type": fieldtype,
				}
			)

	return {
		"fields": fields,
		"data": data,
		"doctype": doctype,
		"docname": docname,
	}


def update_course_statistics():
	courses = frappe.get_all("LMS Course", fields=["name"])

	for course in courses:
		lessons = get_lesson_count(course.name)

		enrollments = frappe.db.count(
			"LMS Enrollment", {"course": course.name, "member_type": "Student"}
		)

		avg_rating = get_average_rating(course.name) or 0
		avg_rating = flt(avg_rating, frappe.get_system_settings("float_precision") or 3)

		frappe.db.set_value(
			"LMS Course",
			course.name,
			{"lessons": lessons, "enrollments": enrollments, "rating": avg_rating},
		)


@frappe.whitelist()
def get_announcements(batch):
	communications = frappe.get_all(
		"Communication",
		filters={
			"reference_doctype": "LMS Batch",
			"reference_name": batch,
		},
		fields=[
			"subject",
			"content",
			"recipients",
			"cc",
			"communication_date",
			"sender",
			"sender_full_name",
		],
		order_by="communication_date desc",
	)

	for communication in communications:
		communication.image = frappe.get_cached_value(
			"User", communication.sender, "user_image"
		)

	return communications


@frappe.whitelist()
def delete_course(course):

	chapters = frappe.get_all("Course Chapter", {"course": course}, pluck="name")

	chapter_references = frappe.get_all(
		"Chapter Reference", {"parent": course}, pluck="name"
	)

	for chapter in chapters:
		lessons = frappe.get_all("Course Lesson", {"chapter": chapter}, pluck="name")

		lesson_references = frappe.get_all(
			"Lesson Reference", {"parent": chapter}, pluck="name"
		)

		for lesson in lesson_references:
			frappe.delete_doc("Lesson Reference", lesson)

		for lesson in lessons:
			topics = frappe.get_all(
				"Discussion Topic",
				{"reference_doctype": "Course Lesson", "reference_docname": lesson},
				pluck="name",
			)

			for topic in topics:
				frappe.db.delete("Discussion Reply", {"topic": topic})

				frappe.db.delete("Discussion Topic", topic)

			frappe.delete_doc("Course Lesson", lesson)

	for chapter in chapter_references:
		frappe.delete_doc("Chapter Reference", chapter)

	for chapter in chapters:
		frappe.delete_doc("Course Chapter", chapter)

	frappe.db.delete("LMS Course Progress", {"course": course})
	frappe.db.delete("LMS Quiz", {"course": course})
	frappe.db.delete("LMS Quiz Submission", {"course": course})
	frappe.db.delete("LMS Enrollment", {"course": course})
	frappe.delete_doc("LMS Course", course)


def give_dicussions_permission():
	doctypes = ["Discussion Topic", "Discussion Reply"]
	roles = ["LMS Student", "Course Creator", "Moderator", "Batch Evaluator"]
	for doctype in doctypes:
		for role in roles:
			if not frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": role}):
				frappe.get_doc(
					{
						"doctype": "Custom DocPerm",
						"parent": doctype,
						"role": role,
						"read": 1,
						"write": 1,
						"create": 1,
						"delete": 1,
					}
				).save(ignore_permissions=True)


@frappe.whitelist()
def upsert_chapter(title, course, is_scorm_package, scorm_package, name=None):
	values = frappe._dict(
		{"title": title, "course": course, "is_scorm_package": is_scorm_package}
	)

	if is_scorm_package:
		scorm_package = frappe._dict(scorm_package)
		extract_path = extract_package(course, title, scorm_package)

		values.update(
			{
				"scorm_package": scorm_package.name,
				"scorm_package_path": extract_path.split("public")[1],
				"manifest_file": get_manifest_file(extract_path).split("public")[1],
				"launch_file": get_launch_file(extract_path).split("public")[1],
			}
		)

	if name:
		chapter = frappe.get_doc("Course Chapter", name)
	else:
		chapter = frappe.new_doc("Course Chapter")

	chapter.update(values)
	chapter.save()

	if is_scorm_package and not len(chapter.lessons):
		add_lesson(title, chapter.name, course)

	return chapter


def extract_package(course, title, scorm_package):
	package = frappe.get_doc("File", scorm_package.name)
	zip_path = package.get_full_path()
	# check_for_malicious_code(zip_path)
	extract_path = frappe.get_site_path("public", "scorm", course, title)
	zipfile.ZipFile(zip_path).extractall(extract_path)
	return extract_path


def check_for_malicious_code(zip_path):
	suspicious_patterns = [
		# Unsafe inline JavaScript
		r'on(click|load|mouseover|error|submit|focus|blur|change|keyup|keydown|keypress|resize)=".*?"',  # Inline event handlers (e.g., onerror, onclick)
		r'<script.*?src=["\']http',  # External script tags
		r"eval\(",  # Usage of eval()
		r"Function\(",  # Usage of Function constructor
		r"(btoa|atob)\(",  # Base64 encoding/decoding
		# Dangerous XML patterns
		r"<!ENTITY",  # XXE-related
		r"<\?xml-stylesheet .*?>",  # External stylesheets in XML
	]

	with zipfile.ZipFile(zip_path, "r") as zf:
		for file_name in zf.namelist():
			if file_name.endswith((".html", ".js", ".xml")):
				with zf.open(file_name) as file:
					content = file.read().decode("utf-8", errors="ignore")
					for pattern in suspicious_patterns:
						if re.search(pattern, content):
							frappe.throw(
								_("Suspicious pattern found in {0}: {1}").format(file_name, pattern)
							)


def get_manifest_file(extract_path):
	manifest_file = None
	for root, dirs, files in os.walk(extract_path):
		for file in files:
			if file == "imsmanifest.xml":
				manifest_file = os.path.join(root, file)
				break
		if manifest_file:
			break
	return manifest_file


def get_launch_file(extract_path):
	launch_file = None
	manifest_file = get_manifest_file(extract_path)

	if manifest_file:
		with open(manifest_file) as file:
			data = file.read()
			dom = parseString(data)
			resource = dom.getElementsByTagName("resource")
			for res in resource:
				if (
					res.getAttribute("adlcp:scormtype") == "sco"
					or res.getAttribute("adlcp:scormType") == "sco"
				):
					launch_file = res.getAttribute("href")
					break

		if launch_file:
			launch_file = os.path.join(os.path.dirname(manifest_file), launch_file)

	return launch_file


def add_lesson(title, chapter, course):
	lesson = frappe.new_doc("Course Lesson")
	lesson.update(
		{
			"title": title,
			"chapter": chapter,
			"course": course,
		}
	)
	lesson.insert()

	lesson_reference = frappe.new_doc("Lesson Reference")
	lesson_reference.update(
		{
			"lesson": lesson.name,
			"parent": chapter,
			"parenttype": "Course Chapter",
			"parentfield": "lessons",
		}
	)
	lesson_reference.insert()


@frappe.whitelist()
def delete_chapter(chapter):
	chapterInfo = frappe.db.get_value(
		"Course Chapter", chapter, ["is_scorm_package", "scorm_package_path"], as_dict=True
	)

	if chapterInfo.is_scorm_package:
		delete_scorm_package(chapterInfo.scorm_package_path)

	frappe.db.delete("Chapter Reference", {"chapter": chapter})
	frappe.db.delete("Lesson Reference", {"parent": chapter})
	frappe.db.delete("Course Lesson", {"chapter": chapter})
	frappe.db.delete("Course Chapter", chapter)


def delete_scorm_package(scorm_package_path):
	scorm_package_path = frappe.get_site_path("public", scorm_package_path[1:])
	if os.path.exists(scorm_package_path):
		shutil.rmtree(scorm_package_path)


@frappe.whitelist()
def mark_lesson_progress(course, chapter_number, lesson_number):
	chapter_name = frappe.get_value(
		"Chapter Reference", {"parent": course, "idx": chapter_number}, "chapter"
	)
	lesson_name = frappe.get_value(
		"Lesson Reference", {"parent": chapter_name, "idx": lesson_number}, "lesson"
	)
	save_progress(lesson_name, course, completed_videos=None)


@frappe.whitelist()
def get_heatmap_data(member=None, base_days=200):
	if not member:
		member = frappe.session.user

	base_date, start_date, number_of_days, days = calculate_date_ranges(base_days)
	date_count = initialize_date_count(days)

	lesson_completions, quiz_submissions, assignment_submissions = fetch_activity_data(
		member, start_date
	)
	count_dates(lesson_completions, date_count)
	count_dates(quiz_submissions, date_count)
	count_dates(assignment_submissions, date_count)

	heatmap_data, labels, total_activities, weeks = prepare_heatmap_data(
		start_date, number_of_days, date_count
	)

	return {
		"heatmap_data": heatmap_data,
		"labels": labels,
		"total_activities": total_activities,
		"weeks": weeks,
	}


def calculate_date_ranges(base_days):
	today = format_date(now(), "YYYY-MM-dd")
	day_today = get_datetime(today).strftime("%w")
	padding_end = 6 - cint(day_today)

	base_date = add_days(today, -base_days)
	day_of_base_date = cint(get_datetime(base_date).strftime("%w"))
	start_date = add_days(base_date, -day_of_base_date)
	number_of_days = base_days + day_of_base_date + padding_end
	days = [add_days(start_date, i) for i in range(number_of_days + 1)]

	return base_date, start_date, number_of_days, days


def initialize_date_count(days):
	return {format_date(day, "YYYY-MM-dd"): 0 for day in days}


def fetch_activity_data(member, start_date):
	lesson_completions = frappe.get_all(
		"LMS Course Progress",
		fields=["creation"],
		filters={"member": member, "creation": [">=", start_date]},
	)

	quiz_submissions = frappe.get_all(
		"LMS Quiz Submission",
		fields=["creation"],
		filters={"member": member, "creation": [">=", start_date]},
	)

	assignment_submissions = frappe.get_all(
		"LMS Assignment Submission",
		fields=["creation"],
		filters={"member": member, "creation": [">=", start_date]},
	)

	return lesson_completions, quiz_submissions, assignment_submissions


def count_dates(data, date_count):
	for entry in data:
		date = format_date(entry.creation, "YYYY-MM-dd")
		if date in date_count:
			date_count[date] += 1


def prepare_heatmap_data(start_date, number_of_days, date_count):
	days_of_week = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
	heatmap_data = {day: [] for day in days_of_week}
	week_count = -(number_of_days // -7)
	labels = [None] * week_count
	last_seen_month = None
	sorted_dates = sorted(date_count.keys())

	for date in sorted_dates:
		activity_count = date_count[date]
		day_of_week = get_datetime(date).strftime("%a")
		current_month = get_datetime(date).strftime("%b")
		column_index = get_week_difference(start_date, date)

		if 0 <= column_index < week_count:
			heatmap_data[day_of_week].append(
				{
					"date": date,
					"count": activity_count,
					"label": f"{activity_count} activities on {format_date(date, 'dd MMM')}",
				}
			)

			if last_seen_month != current_month:
				labels[column_index] = current_month
				last_seen_month = current_month

	for (index, label) in enumerate(labels):
		if not label:
			labels[index] = ""

	formatted_heatmap_data = [
		{"name": day, "data": heatmap_data[day]} for day in days_of_week
	]

	total_activities = sum(date_count.values())
	return formatted_heatmap_data, labels, total_activities, week_count


def get_week_difference(start_date, current_date):
	diff_in_days = date_diff(current_date, start_date)
	return diff_in_days // 7


@frappe.whitelist()
def get_notifications(filters):
	notifications = frappe.get_all(
		"Notification Log",
		filters,
		["subject", "from_user", "link", "read", "name"],
		order_by="creation desc",
	)

	for notification in notifications:
		from_user_details = frappe.db.get_value(
			"User", notification.from_user, ["full_name", "user_image"], as_dict=1
		)
		notification.update(from_user_details)

	return notifications


@frappe.whitelist(allow_guest=True)
def is_guest_allowed():
	return frappe.get_cached_value("LMS Settings", None, "allow_guest_access")


@frappe.whitelist(allow_guest=True)
def is_learning_path_enabled():
	return frappe.get_cached_value("LMS Settings", None, "enable_learning_paths")


@frappe.whitelist()
def cancel_evaluation(evaluation):
	evaluation = frappe._dict(evaluation)

	if evaluation.member != frappe.session.user:
		return

	frappe.db.set_value("LMS Certificate Request", evaluation.name, "status", "Cancelled")
	events = frappe.get_all(
		"Event Participants",
		{
			"email": evaluation.member,
		},
		["parent", "name"],
	)

	for event in events:
		info = frappe.db.get_value("Event", event.parent, ["starts_on", "subject"], as_dict=1)
		date = str(info.starts_on).split(" ")[0]

		if (
			date == str(evaluation.date.format("YYYY-MM-DD"))
			and evaluation.member_name in info.subject
		):
			communication = frappe.db.get_value(
				"Communication",
				{"reference_doctype": "Event", "reference_name": event.parent},
				"name",
			)
			if communication:
				frappe.delete_doc("Communication", communication, ignore_permissions=True)

			frappe.delete_doc("Event Participants", event.name, ignore_permissions=True)
			frappe.delete_doc("Event", event.parent, ignore_permissions=True)


@frappe.whitelist()
def get_certification_details(course):
	membership = None
	filters = {"course": course, "member": frappe.session.user}

	if frappe.db.exists("LMS Enrollment", filters):
		membership = frappe.db.get_value(
			"LMS Enrollment",
			filters,
			["name", "purchased_certificate"],
			as_dict=1,
		)

	paid_certificate = frappe.db.get_value("LMS Course", course, "paid_certificate")
	certificate = frappe.db.get_value(
		"LMS Certificate",
		{"member": frappe.session.user, "course": course},
		["name", "template"],
		as_dict=1,
	)

	return {
		"membership": membership,
		"paid_certificate": paid_certificate,
		"certificate": certificate,
	}


@frappe.whitelist()
def save_role(user, role, value):
	frappe.only_for("Moderator")
	if cint(value):
		doc = frappe.get_doc(
			{
				"doctype": "Has Role",
				"parent": user,
				"role": role,
				"parenttype": "User",
				"parentfield": "roles",
			}
		)
		doc.save(ignore_permissions=True)
	else:
		frappe.db.delete("Has Role", {"parent": user, "role": role})
	return True


@frappe.whitelist()
def add_an_evaluator(email):
	if not frappe.db.exists("User", email):
		user = frappe.new_doc("User")
		user.update(
			{
				"email": email,
				"first_name": email.split("@")[0].capitalize(),
				"enabled": 1,
			}
		)
		user.insert()
		user.add_roles("Batch Evaluator")

	evaluator = frappe.new_doc("Course Evaluator")
	evaluator.evaluator = email
	evaluator.insert()

	return evaluator


@frappe.whitelist()
def capture_user_persona(responses):
	frappe.only_for("System Manager")
	data = frappe.parse_json(responses)
	data = json.dumps(data)
	response = frappe.integrations.utils.make_post_request(
		"https://school.frappe.io/api/method/capture-persona",
		data={"response": data},
	)
	if response.get("message").get("name"):
		frappe.db.set_single_value("LMS Settings", "persona_captured", True)
	return response


@frappe.whitelist()
def get_meta_info(type, route):
	if frappe.db.exists("Website Meta Tag", {"parent": f"{type}/{route}"}):
		meta_tags = frappe.get_all(
			"Website Meta Tag",
			{
				"parent": f"{type}/{route}",
			},
			["name", "key", "value"],
		)

		return meta_tags

	return []


@frappe.whitelist()
def update_meta_info(type, route, meta_tags):
	parent_name = f"{type}/{route}"
	if not isinstance(meta_tags, list):
		frappe.throw(_("Meta tags should be a list."))

	for tag in meta_tags:
		existing_tag = frappe.db.exists(
			"Website Meta Tag",
			{
				"parent": parent_name,
				"parenttype": "Website Route Meta",
				"parentfield": "meta_tags",
				"key": tag["key"],
			},
		)
		if existing_tag:
			if not tag.get("value"):
				frappe.db.delete("Website Meta Tag", existing_tag)
				continue
			frappe.db.set_value("Website Meta Tag", existing_tag, "value", tag["value"])
		elif tag.get("value"):
			tag_properties = {
				"parent": parent_name,
				"parenttype": "Website Route Meta",
				"parentfield": "meta_tags",
				"key": tag["key"],
				"value": tag["value"],
			}

			parent_exists = frappe.db.exists("Website Route Meta", parent_name)
			if not parent_exists:
				route_meta = frappe.new_doc("Website Route Meta")
				route_meta.update(
					{
						"__newname": parent_name,
					}
				)
				route_meta.append("meta_tags", tag_properties)
				route_meta.insert()
			else:
				new_tag = frappe.new_doc("Website Meta Tag")
				new_tag.update(tag_properties)
				print(new_tag)
				new_tag.insert()
				print(new_tag.as_dict())


@frappe.whitelist()
def validate_course_access_before_entry(course_name):
	"""Validate if user can access course before allowing entry"""
	from lms.lms.doctype.lms_enrollment.lms_enrollment import check_course_access
	
	access_result = check_course_access(course_name)
	
	if not access_result.get("access"):
		return {
			"access_denied": True,
			"message": access_result.get("message"),
			"completion_status": access_result.get("completion_status"),
			"completed_on": access_result.get("completed_on")
		}
	
	return {"access_denied": False}


@frappe.whitelist()
def get_course_with_access_check(course_name):
	"""Get course details with access validation"""
	# First check if user can access the course
	access_check = validate_course_access_before_entry(course_name)
	
	if access_check.get("access_denied"):
		return access_check
	
	# If access is allowed, return course details
	course = frappe.get_doc("LMS Course", course_name)
	return {
		"access_denied": False,
		"course": course,
		"enrollment": access_check.get("enrollment")
	}


@frappe.whitelist()
def get_enrollments_with_completion_status(member=None):
	"""Get user enrollments with completion status for dashboard"""
	from lms.lms.doctype.lms_enrollment.lms_enrollment import get_user_course_enrollments
	
	enrollments = get_user_course_enrollments(member)
	
	# Categorize enrollments
	active_courses = []
	completed_courses = []
	re_enrolled_courses = []
	
	for enrollment in enrollments:
		if enrollment.completion_status == "Completed":
			completed_courses.append(enrollment)
		elif enrollment.completion_status == "Re-enrolled":
			re_enrolled_courses.append(enrollment)
		else:
			active_courses.append(enrollment)
	
	return {
		"active_courses": active_courses,
		"completed_courses": completed_courses,
		"re_enrolled_courses": re_enrolled_courses,
		"total_active": len(active_courses),
		"total_completed": len(completed_courses),
		"total_re_enrolled": len(re_enrolled_courses)
	}


@frappe.whitelist()
def admin_re_enroll_user(course_name, member_email, reset_progress=False):
	"""Admin function to re-enroll a user in a course"""
	from lms.lms.doctype.lms_enrollment.lms_enrollment import re_enroll_user_in_course
	
	# Check if current user has permission to re-enroll
	current_user_roles = frappe.get_roles()
	if not any(role in ["System Manager", "Administrator", "Moderator"] for role in current_user_roles):
		frappe.throw(_("You don't have permission to re-enroll users"))
	
	try:
		result = re_enroll_user_in_course(course_name, member_email, reset_progress)
		return result
	except Exception as e:
		frappe.throw(_("Failed to re-enroll user: {0}").format(str(e)))


@frappe.whitelist()
def get_users_for_re_enrollment(course_name=None):
	"""Get list of users who have completed courses and can be re-enrolled"""
	current_user_roles = frappe.get_roles()
	if not any(role in ["System Manager", "Administrator", "Moderator"] for role in current_user_roles):
		frappe.throw(_("You don't have permission to view this data"))

	filters = {
		"completion_status": "Completed",
		"access_restricted": 1
	}

	if course_name:
		filters["course"] = course_name

	completed_enrollments = frappe.get_all(
		"LMS Enrollment",
		filters=filters,
		fields=[
			"name", "member", "member_name", "course", "completed_on",
			"progress", "member_type", "enrollment_version"
		],
		order_by="enrollment_version desc"
	)

	# A member+course accumulates one Completed row per re-enrollment cycle, so the
	# same user would otherwise appear once per historical version. Keep only the
	# latest version per member+course (rows are ordered version-desc), and skip
	# anyone who already has a newer open (Active/Re-enrolled) enrollment.
	seen = set()
	filtered_enrollments = []
	for enrollment in completed_enrollments:
		key = (enrollment.member, enrollment.course)
		if key in seen:
			continue
		seen.add(key)

		# A higher version than this Completed one means the user was already
		# re-enrolled (or reset) and shouldn't be offered for re-enrollment again.
		newer_enrollment = frappe.db.exists(
			"LMS Enrollment",
			{
				"member": enrollment.member,
				"course": enrollment.course,
				"enrollment_version": [">", enrollment.enrollment_version]
			}
		)

		if not newer_enrollment:
			course_title = frappe.db.get_value("LMS Course", enrollment.course, "title")
			enrollment.course_title = course_title
			filtered_enrollments.append(enrollment)

	return filtered_enrollments


@frappe.whitelist()
def bulk_re_enroll_users(enrollments_data):
	"""Bulk re-enroll multiple users"""
	current_user_roles = frappe.get_roles()
	if not any(role in ["System Manager", "Administrator", "Moderator"] for role in current_user_roles):
		frappe.throw(_("You don't have permission to perform bulk re-enrollment"))
	
	enrollments = frappe.parse_json(enrollments_data)
	results = []
	
	for enrollment_data in enrollments:
		try:
			course = enrollment_data.get("course")
			member = enrollment_data.get("member")
			reset_progress = enrollment_data.get("reset_progress", False)
			
			result = admin_re_enroll_user(course, member, reset_progress)
			results.append({
				"course": course,
				"member": member,
				"success": result.get("success"),
				"message": result.get("message")
			})
		except Exception as e:
			results.append({
				"course": enrollment_data.get("course"),
				"member": enrollment_data.get("member"),
				"success": False,
				"message": str(e)
			})
	
	return results


@frappe.whitelist()
def get_course_completion_analytics(course_name=None):
	"""Get analytics data for course completions"""
	current_user_roles = frappe.get_roles()
	if not any(role in ["System Manager", "Administrator", "Moderator"] for role in current_user_roles):
		frappe.throw(_("You don't have permission to view analytics"))
	
	filters = {}
	if course_name:
		filters["course"] = course_name
	
	# Get completion statistics
	total_enrollments = frappe.db.count("LMS Enrollment", filters)
	
	completed_filters = filters.copy()
	completed_filters["completion_status"] = "Completed"
	completed_enrollments = frappe.db.count("LMS Enrollment", completed_filters)
	
	re_enrolled_filters = filters.copy()
	re_enrolled_filters["completion_status"] = "Re-enrolled"
	re_enrolled_count = frappe.db.count("LMS Enrollment", re_enrolled_filters)
	
	# Get completion trend data
	completion_trend = frappe.db.sql("""
		SELECT 
			DATE(completed_on) as completion_date,
			COUNT(*) as completions
		FROM `tabLMS Enrollment`
		WHERE completion_status = 'Completed'
		{course_filter}
		AND completed_on IS NOT NULL
		AND completed_on >= DATE_SUB(NOW(), INTERVAL 30 DAY)
		GROUP BY DATE(completed_on)
		ORDER BY completion_date
	""".format(
		course_filter=f"AND course = '{course_name}'" if course_name else ""
	), as_dict=True)
	
	return {
		"total_enrollments": total_enrollments,
		"completed_enrollments": completed_enrollments,
		"re_enrolled_count": re_enrolled_count,
		"completion_rate": (completed_enrollments / total_enrollments * 100) if total_enrollments > 0 else 0,
		"completion_trend": completion_trend
	}

@frappe.whitelist(allow_guest=True)
def get_course_completion_stats():
	"""
	Get course completion statistics for the dashboard
	"""
	try:
		# Simplify queries to match the working user function pattern
		
		# Total enrolled users - simple count without complex joins
		total_enrolled = frappe.db.sql("""
			SELECT COUNT(*) as count
			FROM `tabLMS Enrollment` e
			WHERE e.docstatus != 2
		""")[0][0] or 0
		
		# Completed courses count - simple query
		completed_courses = frappe.db.sql("""
			SELECT COUNT(*) as count
			FROM `tabLMS Enrollment` e
			WHERE e.completed_on IS NOT NULL
			AND e.docstatus != 2
		""")[0][0] or 0
		
		# Pending completions
		pending_completions = total_enrolled - completed_courses
		
		# Total course reminders sent - simple sum
		total_reminders = frappe.db.sql("""
			SELECT COALESCE(SUM(course_reminder_count), 0) as total
			FROM `tabLMS Enrollment` e
			WHERE e.course_reminder_count IS NOT NULL
			AND e.docstatus != 2
		""")[0][0] or 0
		
		# Reminders sent today
		today = frappe.utils.today()
		reminders_today = frappe.db.sql("""
			SELECT COUNT(*) as count
			FROM `tabEmail Queue`
			WHERE subject LIKE '%Complete your course%'
			AND DATE(creation) = %s
		""", today)[0][0] or 0
		
		# Calculate completion rate
		completion_rate = 0
		if total_enrolled > 0:
			completion_rate = round((completed_courses / total_enrolled) * 100, 1)
		
		# Average time to complete (in days) - simplified
		avg_time_query = frappe.db.sql("""
			SELECT AVG(DATEDIFF(completed_on, creation)) as avg_days
			FROM `tabLMS Enrollment` e
			WHERE e.completed_on IS NOT NULL
			AND e.docstatus != 2
		""")
		avg_time_to_complete = round(avg_time_query[0][0] or 0, 1)
		
		# Most active course - simplified
		most_active_query = frappe.db.sql("""
			SELECT c.title, COUNT(e.name) as enrollment_count
			FROM `tabLMS Course` c
			JOIN `tabLMS Enrollment` e ON c.name = e.course
			WHERE e.docstatus != 2
			GROUP BY c.name, c.title
			ORDER BY enrollment_count DESC
			LIMIT 1
		""", as_dict=True)
		most_active_course = most_active_query[0].title if most_active_query else "N/A"
		
		# Average reminders sent for users with pending completions - simplified
		avg_reminders_query = frappe.db.sql("""
			SELECT AVG(course_reminder_count) as avg_reminders
			FROM `tabLMS Enrollment` e
			WHERE e.completed_on IS NULL
			AND e.course_reminder_count IS NOT NULL
			AND e.course_reminder_count > 0
			AND e.docstatus != 2
		""")
		avg_reminders_sent = round(avg_reminders_query[0][0] or 0, 1)
		
		return {
			"total_enrolled_users": total_enrolled,
			"completed_courses": completed_courses,
			"pending_completions": pending_completions,
			"total_course_reminders_sent": total_reminders,
			"reminders_sent_today": reminders_today,
			"completion_rate": completion_rate,
			"avg_time_to_complete": avg_time_to_complete,
			"most_active_course": most_active_course,
			"avg_reminders_sent": avg_reminders_sent
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting course completion stats: {str(e)}", "Course Stats Error")
		return {
			"total_enrolled_users": 0,
			"completed_courses": 0,
			"pending_completions": 0,
			"total_course_reminders_sent": 0,
			"reminders_sent_today": 0,
			"completion_rate": 0,
			"avg_time_to_complete": 0,
			"most_active_course": "N/A",
			"avg_reminders_sent": 0
		}


@frappe.whitelist(allow_guest=True)
def get_users_with_course_completion_status():
	"""
	Get all users with their course completion status for the dashboard table
	"""
	try:
		users_data = frappe.db.sql("""
			SELECT 
				e.name as enrollment_id,
				e.member as user_id,
				e.course,
				e.creation,
				e.completed_on,
				e.progress,
				e.course_reminder_count,
				e.completion_status,
				e.re_enrolled_on,
				c.title as course_title,
				u.full_name as user_name,
				u.email as user_email
			FROM `tabLMS Enrollment` e
			JOIN `tabLMS Course` c ON e.course = c.name
			JOIN `tabUser` u ON e.member = u.name
			WHERE e.docstatus != 2
			AND u.enabled = 1
			ORDER BY e.creation DESC
		""", as_dict=True)
		
		return users_data
		
	except Exception as e:
		frappe.log_error(f"Error getting users with course completion status: {str(e)}", "Users Status Error")
		return []


@frappe.whitelist(allow_guest=True)
def get_recent_course_completions():
	"""
	Get recent course completions for the dashboard
	"""
	try:
		recent_completions = frappe.db.sql("""
			SELECT 
				e.name as enrollment_id,
				e.member as user_id,
				e.completed_on,
				e.progress,
				c.title as course_title,
				u.full_name as user_name
			FROM `tabLMS Enrollment` e
			JOIN `tabLMS Course` c ON e.course = c.name
			JOIN `tabUser` u ON e.member = u.name
			WHERE e.completed_on IS NOT NULL
			AND e.docstatus != 2
			ORDER BY e.completed_on DESC
			LIMIT 10
		""", as_dict=True)
		
		return recent_completions
		
	except Exception as e:
		frappe.log_error(f"Error getting recent course completions: {str(e)}", "Recent Completions Error")
		return []


@frappe.whitelist(allow_guest=True)
def get_course_reminder_breakdown():
	"""
	Get breakdown of course reminders by count
	"""
	try:
		breakdown_data = frappe.db.sql("""
			SELECT 
				course_reminder_count as count,
				COUNT(*) as users_count
			FROM `tabLMS Enrollment`
			WHERE course_reminder_count IS NOT NULL
			AND course_reminder_count > 0
			AND completed_on IS NULL
			GROUP BY course_reminder_count
			ORDER BY course_reminder_count
		""", as_dict=True)
		
		return breakdown_data
		
	except Exception as e:
		frappe.log_error(f"Error getting course reminder breakdown: {str(e)}", "Reminder Breakdown Error")
		return []


@frappe.whitelist()
def get_enrollments_with_completion_status():
	"""
	Get enrollment data with completion status for course access validation
	"""
	try:
		user = frappe.session.user
		if not user or user == "Guest":
			return {
				"active_courses": [],
				"completed_courses": [],
				"re_enrolled_courses": []
			}
		
		# Get all enrollments for the current user
		enrollments = frappe.db.sql("""
			SELECT 
				e.name,
				e.course,
				e.completed_on,
				e.progress,
				e.re_enrolled_on,
				CASE 
					WHEN e.completed_on IS NOT NULL AND e.re_enrolled_on IS NOT NULL THEN 'Re-enrolled'
					WHEN e.completed_on IS NOT NULL THEN 'Completed'
					ELSE 'Active'
				END as completion_status
			FROM `tabLMS Enrollment` e
			WHERE e.member = %s
			AND e.docstatus != 2
		""", user, as_dict=True)
		
		# Categorize enrollments
		active_courses = []
		completed_courses = []
		re_enrolled_courses = []
		
		for enrollment in enrollments:
			# Reset progress to 0 for re-enrolled courses
			if enrollment.completion_status == 'Re-enrolled':
				enrollment.progress = 0
				re_enrolled_courses.append(enrollment)
			elif enrollment.completion_status == 'Completed':
				completed_courses.append(enrollment)
			else:
				active_courses.append(enrollment)
		
		return {
			"active_courses": active_courses,
			"completed_courses": completed_courses,
			"re_enrolled_courses": re_enrolled_courses
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting enrollments with completion status: {str(e)}", "Enrollment Status Error")
		return {
			"active_courses": [],
			"completed_courses": [],
			"re_enrolled_courses": []
		}


@frappe.whitelist()
def validate_lesson_access(course_name, lesson_name):
	"""
	Validate if a user can access a specific lesson based on completion status
	"""
	try:
		user = frappe.session.user
		if not user or user == "Guest":
			return {"access_granted": False, "message": "Please log in to access lessons"}

		# Check if the lesson is already completed
		progress = frappe.db.exists(
			"LMS Course Progress",
			{
				"course": course_name,
				"lesson": lesson_name,
				"member": user
			}
		)

		if progress:
			# Check enrollment status to see if course is completed and access is restricted
			enrollment = frappe.db.get_value(
				"LMS Enrollment",
				{"member": user, "course": course_name},
				["access_restricted", "completion_status"],
				as_dict=True
			)

			if enrollment and enrollment.get("access_restricted") == 1 and enrollment.get("completion_status") == "Completed":
				return {
					"access_granted": False,
					"message": "This lesson has been completed. Course access is restricted after completion. Please contact the administrator to re-enroll.",
					"lesson_completed": True
				}

		# Allow access if not completed or not restricted
		return {"access_granted": True, "message": "Lesson access granted"}

	except Exception as e:
		frappe.log_error(f"Error validating lesson access: {str(e)}", "Lesson Access Error")
		# In case of error, default to allowing access to avoid blocking users unnecessarily
		return {"access_granted": True, "message": "Lesson access granted (fallback)"}


@frappe.whitelist()
def mark_course_re_enrolled(course_name):
	"""
	Mark a course as re-enrolled and reset progress to 0
	"""
	try:
		user = frappe.session.user
		if not user or user == "Guest":
			return {"success": False, "message": "User not logged in"}
		
		# Get the enrollment
		enrollment = frappe.get_doc("LMS Enrollment", {
			"member": user,
			"course": course_name,
			"docstatus": ("!=", 2)
		})
		
		if not enrollment:
			return {"success": False, "message": "Enrollment not found"}
		
		# Mark as re-enrolled and reset progress
		enrollment.re_enrolled_on = frappe.utils.now_datetime()
		enrollment.progress = 0
		enrollment.completion_status = "Re-enrolled"
		enrollment.access_restricted = 0
		enrollment.current_lesson = None
		enrollment.save(ignore_permissions=True)
		
		# Delete all lesson progress records for this enrollment to start fresh
		frappe.db.sql("""
			DELETE FROM `tabLMS Course Progress`
			WHERE enrollment = %s
		""", enrollment.name)
		
		# Also clean up any orphaned progress records 
		frappe.db.sql("""
			DELETE FROM `tabLMS Course Progress`
			WHERE member = %s 
			AND course = %s
			AND (enrollment IS NULL OR enrollment = '')
		""", (user, course_name))
		
		frappe.db.commit()
		
		return {"success": True, "message": "Course re-enrolled successfully"}
		
	except Exception as e:
		frappe.log_error(f"Error re-enrolling course: {str(e)}", "Re-enrollment Error")
		return {"success": False, "message": "Error during re-enrollment"}


# Keep existing API functions for backward compatibility
@frappe.whitelist()
def get_distributor_login_stats():
	"""
	Legacy function for distributor login stats - kept for backward compatibility
	"""
	try:
		# Total distributors
		total_distributors = frappe.db.count("Distributor", filters={"user_id": ("is", "set")})
		
		# Logged in distributors
		logged_in_distributors = frappe.db.count("Distributor", filters={
			"first_login_date": ("is", "set"),
			"user_id": ("is", "set")
		})
		
		# Never logged in
		never_logged_in = total_distributors - logged_in_distributors
		
		# Total reminders sent
		total_reminders = frappe.db.sql("""
			SELECT COALESCE(SUM(login_reminder_count), 0) as total
			FROM `tabDistributor` 
			WHERE login_reminder_count IS NOT NULL
		""")[0][0] or 0
		
		# Reminders sent today
		today = frappe.utils.today()
		reminders_today = frappe.db.sql("""
			SELECT COUNT(*) as count
			FROM `tabEmail Queue`
			WHERE subject LIKE '%login to Meril Learning Portal%'
			AND DATE(creation) = %s
		""", today)[0][0] or 0
		
		# Calculate response rate
		response_rate = 0
		if total_distributors > 0:
			response_rate = round((logged_in_distributors / total_distributors) * 100, 1)
		
		# Average time to login (in days)
		avg_time_query = frappe.db.sql("""
			SELECT AVG(DATEDIFF(first_login_date, credentials_sent_date)) as avg_days
			FROM `tabDistributor` 
			WHERE first_login_date IS NOT NULL
			AND credentials_sent_date IS NOT NULL
		""")
		avg_time_to_login = round(avg_time_query[0][0] or 0, 1)
		
		# Average reminders sent
		avg_reminders_query = frappe.db.sql("""
			SELECT AVG(login_reminder_count) as avg_reminders
			FROM `tabDistributor`
			WHERE first_login_date IS NULL
			AND login_reminder_count IS NOT NULL
			AND login_reminder_count > 0
		""")
		avg_reminders_sent = round(avg_reminders_query[0][0] or 0, 1)
		
		return {
			"total_distributors": total_distributors,
			"logged_in_distributors": logged_in_distributors,
			"never_logged_in": never_logged_in,
			"total_reminders_sent": total_reminders,
			"reminders_sent_today": reminders_today,
			"response_rate": response_rate,
			"avg_time_to_login": avg_time_to_login,
			"most_effective_day": "Monday",  # Placeholder
			"avg_reminders_sent": avg_reminders_sent
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting distributor login stats: {str(e)}", "Distributor Stats Error")
		return {}


# Fixed function with correct indentation
@frappe.whitelist(allow_guest=True)
def get_distributors_with_login_status():
	"""
	Legacy function for distributor login status - kept for backward compatibility
	"""
	try:
		distributors_data = frappe.db.sql("""
			SELECT 
				d.name,
				d.atendee_name,
				d.distributor_company_name,
				d.distributor_email_address,
				d.user_id,
				d.first_login_date,
				d.last_login_date,
				d.credentials_sent_date,
				d.login_reminder_count
			FROM `tabDistributor` d
			WHERE d.user_id IS NOT NULL
			AND d.user_id != ''
			ORDER BY d.credentials_sent_date DESC
		""", as_dict=True)
		
		return distributors_data
		
	except Exception as e:
		frappe.log_error(f"Error getting distributors with login status: {str(e)}", "Distributors Status Error")
		return []


@frappe.whitelist(allow_guest=True)
def get_recent_distributor_logins():
	"""
	Legacy function for recent distributor logins - kept for backward compatibility
	"""
	try:
		recent_logins = frappe.db.sql("""
			SELECT 
				d.name as distributor_id,
				d.atendee_name as distributor_name,
				d.distributor_company_name as company_name,
				d.last_login_date,
				CASE 
					WHEN d.first_login_date = d.last_login_date THEN 1
					ELSE 0
				END as is_first_login
			FROM `tabDistributor` d
			WHERE d.last_login_date IS NOT NULL
			ORDER BY d.last_login_date DESC
			LIMIT 10
		""", as_dict=True)
		
		return recent_logins
		
	except Exception as e:
		frappe.log_error(f"Error getting recent distributor logins: {str(e)}", "Recent Logins Error")
		return []


@frappe.whitelist()
def get_reminder_breakdown():
	"""
	Legacy function for reminder breakdown - kept for backward compatibility
	"""
	try:
		breakdown_data = frappe.db.sql("""
			SELECT 
				login_reminder_count as count,
				COUNT(*) as distributors_count
			FROM `tabDistributor`
			WHERE login_reminder_count IS NOT NULL
			AND login_reminder_count > 0
			AND first_login_date IS NULL
			GROUP BY login_reminder_count
			ORDER BY login_reminder_count
		""", as_dict=True)
		
		return breakdown_data
		
	except Exception as e:
		frappe.log_error(f"Error getting reminder breakdown: {str(e)}", "Reminder Breakdown Error")
		return []


@frappe.whitelist()
def migrate_lesson_progress_to_enrollment_based():
	"""
	Migration function to update existing LMS Course Progress records 
	to link them to enrollments and ensure data consistency
	"""
	try:
		# Get all LMS Course Progress records that don't have enrollment links
		orphaned_progress = frappe.db.sql("""
			SELECT 
				lcp.name,
				lcp.member,
				lcp.course,
				lcp.lesson,
				lcp.status,
				e.name as enrollment_id
			FROM `tabLMS Course Progress` lcp
			LEFT JOIN `tabLMS Enrollment` e ON (
				lcp.member = e.member 
				AND lcp.course = e.course
			)
			WHERE lcp.enrollment IS NULL OR lcp.enrollment = ''
		""", as_dict=True)
		
		updated_count = 0
		deleted_count = 0
		
		for progress in orphaned_progress:
			if progress.enrollment_id:
				# Link to existing enrollment
				frappe.db.sql("""
					UPDATE `tabLMS Course Progress`
					SET enrollment = %s,
						is_complete = %s,
						progress = %s,
						completed_on = %s
					WHERE name = %s
				""", (
					progress.enrollment_id,
					1 if progress.status == "Complete" else 0,
					100 if progress.status == "Complete" else 0,
					frappe.utils.now_datetime() if progress.status == "Complete" else None,
					progress.name
				))
				updated_count += 1
			else:
				# No enrollment found, delete orphaned progress
				frappe.db.delete("LMS Course Progress", progress.name)
				deleted_count += 1
		
		frappe.db.commit()
		
		return {
			"success": True,
			"message": f"Migration completed: {updated_count} records updated, {deleted_count} orphaned records deleted"
		}
		
	except Exception as e:
		frappe.log_error(f"Error during lesson progress migration: {str(e)}", "Migration Error")
		return {
			"success": False,
			"message": f"Migration failed: {str(e)}"
		}


@frappe.whitelist()
def recalculate_course_progress_for_all():
	"""
	Recalculate course progress for all enrollments based on lesson completion
	"""
	try:
		from lms.lms.utils import get_course_progress
		
		enrollments = frappe.get_all("LMS Enrollment", 
			fields=["name", "course", "member"],
			filters={"docstatus": ("!=", 2)}
		)
		
		updated_count = 0
		
		for enrollment in enrollments:
			try:
				# Recalculate progress
				new_progress = get_course_progress(enrollment.course, enrollment.member)
				
				# Update enrollment
				frappe.db.set_value("LMS Enrollment", enrollment.name, "progress", max(0, min(100, new_progress)))
				
				# Check if course should be marked as completed
				enrollment_doc = frappe.get_doc("LMS Enrollment", enrollment.name)
				enrollment_doc.check_course_completion()
				
				updated_count += 1
				
			except Exception as e:
				frappe.log_error(f"Error updating progress for enrollment {enrollment.name}: {str(e)}", "Progress Recalculation Error")
				continue
		
		frappe.db.commit()
		
		return {
			"success": True,
			"message": f"Progress recalculated for {updated_count} enrollments"
		}
		
	except Exception as e:
		frappe.log_error(f"Error during progress recalculation: {str(e)}", "Progress Recalculation Error")
		return {
			"success": False,
			"message": f"Progress recalculation failed: {str(e)}"
		}


@frappe.whitelist(allow_guest=False)
def register_push_token(user_id, token, device_id=None):
	"""Register or update mobile push token for a user"""
	try:
		# Log the incoming request for debugging
		frappe.log_error(
			f"register_push_token called with user_id: {user_id}, token: {token[:50] if token else 'None'}...",
			"Push Token Debug",
		)
		frappe.log_error(f"Session user: {frappe.session.user}", "Push Token Debug - Session")

		if not user_id or not token:
			frappe.log_error(f"Missing data - user_id: {user_id}, token: {token}", "Push Token Error")
			frappe.throw(_("User ID and token are required"))

		# Check if the user is authenticated
		if frappe.session.user == "Guest":
			frappe.log_error("User is Guest - authentication required", "Push Token Error")
			frappe.throw(_("Authentication required"))

		# Allow both exact match and Administrator to register tokens
		if user_id != frappe.session.user and frappe.session.user != "Administrator":
			frappe.log_error(f"User mismatch - user_id: {user_id}, session: {frappe.session.user}", "Push Token Error")
			frappe.throw(_("You can only register tokens for your own account"))

		# Check if a token already exists for this user
		existing_token = frappe.db.get_value(
			"Mobile Push Token",
			{"user_id": user_id},
			"name",
		)

		frappe.log_error(f"Existing token check - Found: {existing_token}", "Push Token Debug")

		if existing_token:
			# Update existing token
			doc = frappe.get_doc("Mobile Push Token", existing_token)
			frappe.log_error(f"Existing doc - user_id: {doc.user_id}, old_token: {doc.token[:50] if doc.token else 'None'}...", "Push Token Debug")

			if doc.token != token:
				doc.token = token
				doc.save(ignore_permissions=True)
				frappe.db.commit()
				frappe.log_error(f"Token updated for user {user_id} - Token: {token[:50]}...", "Push Token Update Success")
				return {
					"success": True,
					"message": _("Push token updated successfully"),
					"action": "updated",
					"doc_name": doc.name
				}
			else:
				frappe.log_error(f"Token already exists and is same for user {user_id}", "Push Token Info")
				return {
					"success": True,
					"message": _("Token already registered"),
					"action": "exists"
				}
		else:
			# Check if this token is already registered for another user
			duplicate_token = frappe.db.get_value(
				"Mobile Push Token",
				{"token": token},
				["name", "user_id"],
				as_dict=True,
			)

			if duplicate_token:
				# Token exists for another user, update it
				if duplicate_token.user_id != user_id:
					doc = frappe.get_doc("Mobile Push Token", duplicate_token.name)
					doc.user_id = user_id
					doc.token = token
					doc.save(ignore_permissions=True)
					frappe.db.commit()
					return {
						"success": True,
						"message": _("Push token reassigned successfully"),
						"action": "reassigned",
					}
				else:
					return {
						"success": True,
						"message": _("Token already registered"),
						"action": "exists",
					}

			# Create new token entry
			frappe.log_error(f"Creating new token for user {user_id}", "Push Token Debug")
			doc = frappe.new_doc("Mobile Push Token")
			doc.user_id = user_id
			doc.token = token
			doc.insert(ignore_permissions=True)
			frappe.db.commit()
			frappe.log_error(f"New token created for user {user_id} - Doc Name: {doc.name}, Token: {token[:50]}...", "Push Token Create Success")

			return {
				"success": True,
				"message": _("Push token registered successfully"),
				"action": "created",
				"doc_name": doc.name
			}

	except Exception as e:
		frappe.log_error(f"Error registering push token: {str(e)}", "Push Token Registration Error")
		return {
			"success": False,
			"message": str(e)
		}


@frappe.whitelist()
def unregister_push_token(device_id=None, token=None):
	"""Unregister a push token"""
	try:
		if not token:
			frappe.throw(_("Token is required"))

		filters = {"user_id": frappe.session.user, "token": token}

		token_doc = frappe.db.get_value("Mobile Push Token", filters, "name")

		if token_doc:
			frappe.delete_doc("Mobile Push Token", token_doc, ignore_permissions=True)
			frappe.db.commit()
			return {
				"success": True,
				"message": _("Push token unregistered successfully")
			}
		else:
			return {
				"success": False,
				"message": _("Token not found")
			}

	except Exception as e:
		frappe.log_error(f"Error unregistering push token: {str(e)}", "Push Token Unregistration Error")
		return {
			"success": False,
			"message": str(e)
		}


@frappe.whitelist(allow_guest=True)
def serve_pdf_inline(file_url):
	"""
	Enhanced PDF serving with proper headers for all devices.
	Detects device type and adjusts headers accordingly.
	"""
	import os
	from frappe.utils.file_manager import get_file_path

	try:
		# Get user agent for device detection
		user_agent = frappe.get_request_header("User-Agent") or ""

		# Detect device type
		is_mobile = any(device in user_agent for device in [
			"Android", "iPhone", "iPad", "iPod", "Mobile", "mobile", "Windows Phone"
		])

		is_ios = "iPhone" in user_agent or "iPad" in user_agent or "iPod" in user_agent
		is_android = "Android" in user_agent
		is_webview = "wv" in user_agent or "WebView" in user_agent

		# Clean the file URL
		if file_url.startswith('/'):
			file_url = file_url[1:]

		# Get the actual file path
		file_path = get_file_path(file_url)

		if not os.path.exists(file_path):
			frappe.response["http_status_code"] = 404
			return {"error": "File not found"}

		# Get file size for range requests support
		file_size = os.path.getsize(file_path)

		# Check for range request (important for iOS)
		range_header = frappe.get_request_header("Range")
		if range_header:
			# Parse range header
			import re
			range_match = re.search(r'bytes=(\d+)-(\d*)', range_header)
			if range_match:
				start = int(range_match.group(1))
				end = int(range_match.group(2)) if range_match.group(2) else file_size - 1

				# Read the requested range
				with open(file_path, 'rb') as f:
					f.seek(start)
					file_content = f.read(end - start + 1)

				# Set 206 Partial Content response
				frappe.response["http_status_code"] = 206
				frappe.local.response.filecontent = file_content
				frappe.local.response.type = "pdf"

				# Set range headers
				frappe.local.response.headers = {
					"Content-Type": "application/pdf",
					"Content-Length": str(len(file_content)),
					"Content-Range": f"bytes {start}-{end}/{file_size}",
					"Accept-Ranges": "bytes",
					"Content-Disposition": f'inline; filename="{os.path.basename(file_path)}"',
					"Cache-Control": "public, max-age=3600",
				}
				return

		# Read the full file content
		with open(file_path, 'rb') as f:
			file_content = f.read()

		# Set proper headers based on device type
		frappe.local.response.filename = os.path.basename(file_path)
		frappe.local.response.filecontent = file_content
		frappe.local.response.type = "pdf"

		# Build headers based on device
		headers = {
			"Content-Type": "application/pdf",
			"Content-Length": str(file_size),
			"Accept-Ranges": "bytes",  # Enable range requests
			"X-Content-Type-Options": "nosniff",
		}

		# Adjust Content-Disposition based on device
		if is_ios:
			# iOS requires specific inline handling with proper CORS
			headers["Content-Disposition"] = f'inline; filename="{os.path.basename(file_path)}"'
			headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
			headers["X-Frame-Options"] = "SAMEORIGIN"
			headers["Access-Control-Allow-Origin"] = "*"
			headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
		elif is_android and is_webview:
			# Android WebView needs different handling
			headers["Content-Disposition"] = f'inline; filename="{os.path.basename(file_path)}"'
			headers["Cache-Control"] = "public, max-age=3600"
			headers["X-Frame-Options"] = "SAMEORIGIN"
			headers["Access-Control-Allow-Origin"] = "*"
		elif is_mobile:
			# General mobile handling with better compatibility
			headers["Content-Disposition"] = f'inline; filename="{os.path.basename(file_path)}"'
			headers["Cache-Control"] = "public, max-age=3600"
			headers["X-Frame-Options"] = "SAMEORIGIN"
			headers["Access-Control-Allow-Origin"] = "*"
			headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
			# Add viewport support hint
			headers["X-Mobile-Optimized"] = "width=device-width"
		else:
			# Desktop handling
			headers["Content-Disposition"] = f'inline; filename="{os.path.basename(file_path)}"'
			headers["Cache-Control"] = "public, max-age=86400"

		# Add CORS headers for cross-origin requests
		headers["Access-Control-Allow-Origin"] = "*"
		headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
		headers["Access-Control-Allow-Headers"] = "Range, Content-Type"

		frappe.local.response.headers = headers
		return

	except Exception as e:
		frappe.log_error(f"Error serving PDF inline: {str(e)}", "PDF Serve Error")
		frappe.response["http_status_code"] = 500
		return {"error": str(e)}


@frappe.whitelist(allow_guest=True)
def get_document_info(file_url):
	"""
	Get document information for better client-side handling
	"""
	import os
	from frappe.utils.file_manager import get_file_path

	try:
		if file_url.startswith('/'):
			file_url = file_url[1:]

		file_path = get_file_path(file_url)

		if not os.path.exists(file_path):
			return {"error": "File not found", "exists": False}

		file_size = os.path.getsize(file_path)
		file_extension = os.path.splitext(file_path)[1].lower()

		return {
			"exists": True,
			"size": file_size,
			"size_mb": round(file_size / (1024 * 1024), 2),
			"extension": file_extension,
			"name": os.path.basename(file_path),
			"mime_type": mimetypes.guess_type(file_path)[0] or "application/octet-stream"
		}

	except Exception as e:
		frappe.log_error(f"Error getting document info: {str(e)}", "Document Info Error")
		return {"error": str(e), "exists": False}


@frappe.whitelist()
def portal_reset_course(course_name, batch_size=200):
	"""Start a Portal Reset for a course.

	This no longer runs synchronously. It creates a `Portal Reset Job`, enqueues a
	background worker on the `long` queue, and returns immediately so the request
	never times out regardless of dataset size. Callers poll `portal_reset_status`
	(or subscribe to the `portal_reset_progress` realtime event) for progress.

	Historical compliance data (course progress, quiz/assignment attempts, document
	submissions, enrollment history) is archived into `Portal Reset Archive` before
	the active cycle state is cleared — nothing is permanently deleted.
	"""
	from lms.lms.portal_reset.api import start_portal_reset

	return start_portal_reset(course_name, batch_size)


@frappe.whitelist()
def portal_reset_status(job=None, course_name=None):
	"""Return progress for a Portal Reset Job.

	Accepts either an explicit `job` name or a `course_name` (in which case the
	latest active job for that course is used). Shape is stable for the monitoring
	UI to poll.
	"""
	from lms.lms.portal_reset.api import get_portal_reset_job

	if not job and course_name:
		job = frappe.db.get_value(
			"Portal Reset Job",
			{"course": course_name},
			"name",
			order_by="creation desc",
		)
	if not job:
		return {"status": "idle", "finished": True}
	return get_portal_reset_job(job)


@frappe.whitelist()
def get_courses_for_portal_reset():
	"""Return all published LMS courses for the portal reset dropdown"""
	courses = frappe.get_all(
		"LMS Course",
		filters={"published": 1},
		fields=["name", "title"],
		order_by="title"
	)
	return [{"label": c.title, "value": c.name} for c in courses]


def auto_enroll_on_course_publish(doc, method):
	"""
	Called on LMS Course.on_update.
	When a course is newly published, auto-enroll all eligible distributors and employees.
	Eligibility: country is in the course's Option Country child table,
	and the course is assigned to the matching role.
	"""
	if not doc.published:
		return

	# Only act when the course transitions to published
	if not doc.has_value_changed("published"):
		return

	try:
		course_name = doc.name
		assigned_role = getattr(doc, "custom_assigned_to_role", None)  # "Distributor", "Employee", or "All"

		# Get countries assigned to this course
		assigned_countries = frappe.get_all(
			"Option Country",
			filters={"parent": course_name, "parenttype": "LMS Course"},
			pluck="country"
		)

		# Course eligibility is country-based. If no countries are configured, there is
		# no valid eligibility criteria, so no one should be auto-enrolled.
		# (A future explicit "all countries" flag could bypass this, but none exists yet.)
		if not assigned_countries:
			frappe.logger().info(
				f"No countries assigned to course '{course_name}'; skipping auto-enrollment to avoid mass-enrolling all users."
			)
			return

		enrolled_count = 0

		# Enroll distributors
		if assigned_role in ("Distributor", "All", None):
			distributors = frappe.get_all(
				"Distributor",
				filters={"user_id": ("is", "set")},
				fields=["name", "user_id", "country", "distributor_email_address"]
			)
			for dist in distributors:
				if dist.country not in assigned_countries:
					continue
				user_id = dist.user_id
				# Skip if already enrolled
				if frappe.db.exists("LMS Enrollment", {"member": user_id, "course": course_name}):
					continue
				try:
					enrollment = frappe.new_doc("LMS Enrollment")
					enrollment.update({
						"member": user_id,
						"course": course_name,
						"member_type": "Student",
						"completion_status": "Active",
						"access_restricted": 0,
						"progress": 0,
					})
					enrollment.insert(ignore_permissions=True)
					enrolled_count += 1
				except Exception as e:
					frappe.log_error(f"Auto-enroll distributor {user_id} in {course_name}: {str(e)}", "Auto Enroll Error")

		# Enroll employees
		if assigned_role in ("Employee", "All", None):
			employees = frappe.get_all(
				"Employee",
				filters={"user_id": ("is", "set")},
				fields=["name", "user_id", "country"]
			)
			for emp in employees:
				if emp.country not in assigned_countries:
					continue
				user_id = emp.user_id
				if frappe.db.exists("LMS Enrollment", {"member": user_id, "course": course_name}):
					continue
				try:
					enrollment = frappe.new_doc("LMS Enrollment")
					enrollment.update({
						"member": user_id,
						"course": course_name,
						"member_type": "Student",
						"completion_status": "Active",
						"access_restricted": 0,
						"progress": 0,
					})
					enrollment.insert(ignore_permissions=True)
					enrolled_count += 1
				except Exception as e:
					frappe.log_error(f"Auto-enroll employee {user_id} in {course_name}: {str(e)}", "Auto Enroll Error")

		frappe.db.commit()
		frappe.logger().info(f"Auto-enrolled {enrolled_count} users in new course '{course_name}'")

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Auto Enroll on Course Publish Error")

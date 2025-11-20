# Copyright (c) 2021, FOSS United and contributors
# For license information, please see license.txt

import frappe
import json
from frappe import _
from frappe.model.document import Document
from frappe.utils.telemetry import capture
from lms.lms.utils import get_course_progress
from ...md import find_macros
from frappe.realtime import get_website_room


class CourseLesson(Document):
	def on_update(self):
		self.validate_quiz_id()

	def validate_quiz_id(self):
		if self.quiz_id and not frappe.db.exists("LMS Quiz", self.quiz_id):
			frappe.throw(_("Invalid Quiz ID"))

		if self.content:
			self.save_lesson_details_in_quiz(self.content)

		if self.instructor_content:
			self.save_lesson_details_in_quiz(self.instructor_content)

	def save_lesson_details_in_quiz(self, content):
		content = json.loads(self.content)
		for block in content.get("blocks"):
			if block.get("type") == "quiz":
				quiz = block.get("data").get("quiz")
				if not frappe.db.exists("LMS Quiz", quiz):
					frappe.throw(_("Invalid Quiz ID in content"))
				frappe.db.set_value(
					"LMS Quiz",
					quiz,
					{
						"course": self.course,
						"lesson": self.name,
					},
				)


def normalize_url(url):
    return url.lower().rstrip('/') if url else url

def lesson_has_quizzes(lesson):
	"""Check if a lesson has any quizzes"""
	lesson_details = frappe.db.get_value(
		"Course Lesson", lesson, ["body", "content"], as_dict=1
	)
	quizzes = []

	if lesson_details and lesson_details.content:
		try:
			content = json.loads(lesson_details.content)
			for block in content.get("blocks", []):
				if block.get("type") == "quiz":
					quizzes.append(block.get("data").get("quiz"))
				if block.get("type") == "upload":
					quizzes_in_video = block.get("data", {}).get("quizzes")
					if quizzes_in_video and len(quizzes_in_video) > 0:
						for row in quizzes_in_video:
							quizzes.append(row.get("quiz"))
		except Exception:
			pass

	elif lesson_details and lesson_details.body:
		macros = find_macros(lesson_details.body)
		quizzes = [value for name, value in macros if name == "Quiz"]

	return len(quizzes) > 0

@frappe.whitelist()
def save_progress(lesson, course, completed_videos=None):
	latest_enrollment = frappe.get_all(
		"LMS Enrollment",
		filters={"course": course, "member": frappe.session.user},
		fields=["name"],
		order_by="enrollment_version desc, creation desc",
		limit=1,
	)
	membership = latest_enrollment[0].name if latest_enrollment else None
	if not membership:
		return 0

	frappe.db.set_value("LMS Enrollment", membership, "current_lesson", lesson)
	
	# Get current progress before any updates
	current_progress = get_course_progress(course)
	
	# Check if progress already exists for this enrollment and lesson
	existing_progress_name = frappe.db.exists(
		"LMS Course Progress", {
			"lesson": lesson, 
			"member": frappe.session.user,
			"enrollment": membership
		}
	)
	already_completed = bool(existing_progress_name)
	
	# Check if lesson has quizzes - if yes, quiz must be passed
	has_quizzes = lesson_has_quizzes(lesson)
	if has_quizzes:
		# If user has 'Distributor' role but not 'Administrator', treat quiz as completed
		roles = frappe.get_roles(frappe.session.user)
		if "Distributor" in roles and "Administrator" not in roles:
			quiz_completed = True
		else:
			quiz_completed = get_quiz_progress(lesson)
		
		# If quiz exists but not passed, don't update progress - return current progress
		if not quiz_completed:
			frappe.logger().info(f"[save_progress] Quiz not passed for lesson {lesson}, progress unchanged")
			return current_progress
	else:
		# No quizzes in lesson, quiz requirement is satisfied
		quiz_completed = True
	
	# Check assignment progress
	assignment_completed = get_assignment_progress(lesson)

	# --- Video completion logic ---
	video_urls = [normalize_url(url) for url in get_lesson_video_urls(lesson)]
	all_videos_completed = True
	completed_videos_list = []
	if completed_videos:
		try:
			completed_videos_list = json.loads(completed_videos) if isinstance(completed_videos, str) else completed_videos
		except Exception:
			completed_videos_list = []
	completed_videos_list = [normalize_url(url) for url in completed_videos_list]
	if video_urls:
		# If there are videos, require all to be completed
		all_videos_completed = set(video_urls) <= set(completed_videos_list)
	frappe.logger().info(f"[save_progress] video_urls: {video_urls}")
	frappe.logger().info(f"[save_progress] completed_videos_list: {completed_videos_list}")
	frappe.logger().info(f"[save_progress] all_videos_completed: {all_videos_completed}")
	# --- End video logic ---

	# Only update progress if all requirements are met
	all_requirements_met = quiz_completed and assignment_completed and (not video_urls or all_videos_completed)
	
	if not all_requirements_met:
		# Requirements not met, return current progress without updating
		frappe.logger().info(f"[save_progress] Requirements not met for lesson {lesson}, progress unchanged")
		return current_progress

	# All requirements met - update or create progress record
	if already_completed:
		progress_doc = frappe.get_doc("LMS Course Progress", existing_progress_name)
		progress_doc.status = "Complete"
		progress_doc.is_complete = 1
		progress_doc.progress = 100
		progress_doc.completed_on = frappe.utils.now_datetime()
		if completed_videos_list:
			progress_doc.completed_videos = json.dumps(completed_videos_list)
		progress_doc.save(ignore_permissions=True)
	else:
		# Create progress record linked to enrollment
		progress_doc = frappe.get_doc({
			"doctype": "LMS Course Progress",
			"lesson": lesson,
			"status": "Complete",
			"member": frappe.session.user,
			"enrollment": membership,
			"completed_on": frappe.utils.now_datetime(),
			"is_complete": 1,
			"progress": 100,
			"completed_videos": json.dumps(completed_videos_list) if completed_videos_list else None
		})
		progress_doc.save(ignore_permissions=True)

	# Recalculate course progress after updating lesson progress
	progress = get_course_progress(course)
	capture_progress_for_analytics(progress, course)

	# Update enrollment progress and check completion
	enrollment = frappe.get_doc("LMS Enrollment", membership)
	previous_progress = enrollment.progress or 0
	enrollment.progress = progress
	enrollment.save()
	enrollment.run_method("on_change")

	# Auto-create course documents when course reaches 100% completion
	if progress == 100 and previous_progress < 100:
		try:
			# Import the function from documents module
			from lms.overrides.documents import create_course_documents_on_completion
			create_course_documents_on_completion(
				user=frappe.session.user,
				course=course,
				enrollment_name=membership
			)
		except Exception as e:
			# Log error but don't fail the lesson progress update
			frappe.log_error(f"Error creating course documents on completion: {str(e)}")

	frappe.publish_realtime(
		event="update_lesson_progress",
		room=get_website_room(),
		message={"course": course, "lesson": lesson, "progress": progress},
		after_commit=True,
	)

	return progress


def capture_progress_for_analytics(progress, course):
	if progress in [25, 50, 75, 100]:
		capture("course_progress", "lms", properties={"course": course, "progress": progress})


def get_quiz_progress(lesson):
	lesson_details = frappe.db.get_value(
		"Course Lesson", lesson, ["body", "content"], as_dict=1
	)
	quizzes = []

	if lesson_details.content:
		content = json.loads(lesson_details.content)

		for block in content.get("blocks"):
			if block.get("type") == "quiz":
				quizzes.append(block.get("data").get("quiz"))
			if block.get("type") == "upload":
				quizzes_in_video = block.get("data").get("quizzes")
				if quizzes_in_video and len(quizzes_in_video) > 0:
					for row in quizzes_in_video:
						quizzes.append(row.get("quiz"))

	elif lesson_details.body:
		macros = find_macros(lesson_details.body)
		quizzes = [value for name, value in macros if name == "Quiz"]

	for quiz in quizzes:
		passing_percentage = frappe.db.get_value("LMS Quiz", quiz, "passing_percentage")
		if not frappe.db.exists(
			"LMS Quiz Submission",
			{
				"quiz": quiz,
				"member": frappe.session.user,
				"percentage": [">=", passing_percentage],
			},
		):
			return False
	return True


def get_assignment_progress(lesson):
	lesson_details = frappe.db.get_value(
		"Course Lesson", lesson, ["body", "content"], as_dict=1
	)
	assignments = []

	if lesson_details.content:
		content = json.loads(lesson_details.content)

		for block in content.get("blocks"):
			if block.get("type") == "assignment":
				assignments.append(block.get("data").get("assignment"))

	elif lesson_details.body:
		macros = find_macros(lesson_details.body)
		assignments = [value for name, value in macros if name == "Assignment"]

	for assignment in assignments:
		if not frappe.db.exists(
			"LMS Assignment Submission",
			{"assignment": assignment, "member": frappe.session.user},
		):
			return False
	return True


@frappe.whitelist()
def get_lesson_info(chapter):
	return frappe.db.get_value("Course Chapter", chapter, "course")


def get_lesson_video_urls(lesson):
	lesson_details = frappe.db.get_value(
		"Course Lesson", lesson, ["body", "content"], as_dict=1
	)
	video_urls = []
	if lesson_details.content:
		try:
			content = json.loads(lesson_details.content)
			for block in content.get("blocks", []):
				if block.get("type") == "upload":
					data = block.get("data", {})
					file_type = data.get("file_type", "").lower()
					if file_type in ["mp4", "mov", "avi", "mkv", "webm"]:
						url = data.get("file_url")
						if url:
							video_urls.append(url)
		except Exception:
			pass
	# Optionally, parse body for legacy video macros if needed
	return video_urls

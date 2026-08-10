# Copyright (c) 2021, FOSS United and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from lms.lms.utils import get_course_progress, get_current_enrollment_name
from lms.lms.api import update_course_statistics


class CourseChapter(Document):
	def on_update(self):
		self.recalculate_course_progress()
		update_course_statistics()

	def recalculate_course_progress(self):
		previous_lessons = (
			self.get_doc_before_save() and self.get_doc_before_save().as_dict().lessons
		)
		current_lessons = self.lessons

		if previous_lessons and previous_lessons != current_lessons:
			enrolled_members = frappe.get_all(
				"LMS Enrollment", {"course": self.course}, pluck="member", distinct=True
			)
			for member in enrolled_members:
				enrollment = get_current_enrollment_name(self.course, member)
				if not enrollment:
					continue
				new_progress = get_course_progress(self.course, member)
				frappe.db.set_value("LMS Enrollment", enrollment, "progress", max(0, min(100, new_progress)))

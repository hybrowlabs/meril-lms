# Copyright (c) 2021, FOSS United and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from lms.lms.utils import get_course_progress, get_current_enrollment_name


class LMSCourseProgress(Document):
	def after_delete(self):
		membership = get_current_enrollment_name(self.course, self.member)
		if not membership:
			return

		progress = get_course_progress(self.course, self.member)
		frappe.db.set_value("LMS Enrollment", membership, "progress", max(0, min(100, progress)))

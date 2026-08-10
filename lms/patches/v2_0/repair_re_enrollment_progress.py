import frappe
from frappe.utils import cint, flt

from lms.lms.utils import get_lessons


def execute():
	"""Rebuild progress on the current enrollment of every re-enrolled learner.

	Re-enrollments performed before the current-enrollment fix could leave the
	newest enrollment row holding the previous cycle's progress, and a
	"Completed" status that locks the learner out of the cycle they were just
	re-enrolled into. Course progress records are scoped to an enrollment, so the
	stored value is simply rebuilt from them; rows that already agree are left
	untouched, which makes this patch safe to re-run.
	"""
	precision = cint(frappe.db.get_default("float_precision")) or 3
	lesson_counts = {}
	repaired_progress = repaired_status = 0
	still_locked = certified_but_incomplete = 0

	for enrollment in get_current_enrollments():
		if enrollment.course not in lesson_counts:
			lesson_counts[enrollment.course] = get_lessons(enrollment.course, get_details=False)

		lesson_count = lesson_counts[enrollment.course]
		if not lesson_count:
			continue

		completed_lessons = frappe.db.count(
			"LMS Course Progress",
			{"enrollment": enrollment.name, "status": "Complete", "is_complete": 1},
		)
		progress = flt(max(0, min(100, (completed_lessons / lesson_count) * 100)), precision)

		if flt(enrollment.progress, precision) != progress:
			frappe.db.set_value(
				"LMS Enrollment", enrollment.name, "progress", progress, update_modified=False
			)
			repaired_progress += 1

		# A stale "Completed" also carries access_restricted, which bars the learner
		# from the new cycle. Both are cleared together so access is actually restored.
		if progress < 100 and enrollment.completion_status == "Completed":
			frappe.db.set_value(
				"LMS Enrollment",
				enrollment.name,
				{"completion_status": "Re-enrolled", "access_restricted": 0},
				update_modified=False,
			)
			repaired_status += 1
		elif progress < 100 and enrollment.access_restricted:
			still_locked += 1

		if progress < 100 and enrollment.is_certified:
			certified_but_incomplete += 1

	print(
		f"repair_re_enrollment_progress: progress repaired on {repaired_progress} enrollment(s), "
		f"status repaired on {repaired_status}"
	)
	if still_locked:
		print(
			f"repair_re_enrollment_progress: {still_locked} incomplete enrollment(s) remain "
			f"access_restricted without a stale status - review manually"
		)
	if certified_but_incomplete:
		print(
			f"repair_re_enrollment_progress: {certified_but_incomplete} incomplete enrollment(s) "
			f"are still flagged is_certified - left untouched, review manually"
		)


def get_current_enrollments():
	"""Latest enrollment row of every member+course that has been re-enrolled."""
	return frappe.db.sql(
		"""
		SELECT name, course, progress, completion_status, access_restricted, is_certified
		FROM (
			SELECT name, course, progress, completion_status, access_restricted, is_certified,
				ROW_NUMBER() OVER (PARTITION BY member, course
					ORDER BY enrollment_version DESC, creation DESC) AS rn,
				COUNT(*) OVER (PARTITION BY member, course) AS cycles
			FROM `tabLMS Enrollment`
		) enrollments
		WHERE rn = 1 AND cycles > 1
		""",
		as_dict=True,
	)

import frappe


def execute():
	"""Fill submission_datetime on Employee Course Documents completed before the fix.

	The completion handler used to write `submission_date` — a fieldname that does
	not exist on the doctype, so Frappe dropped it silently — and it skipped the
	record entirely whenever one had already been created at enrollment. Between
	the two, no employee document ever carried a submission date.

	The date those records should hold is the course completion date, taken from
	two sources in order of authority:

	1. `LMS Enrollment.completed_on` — the completion the enrollment itself
	   recorded. Exact, but only written once the learner certifies.
	2. The last `LMS Course Progress.completed_on` of that enrollment — when the
	   final lesson was finished. This exists whether or not the learner ever
	   certified, and for an uncertified learner it is the closest thing to a real
	   completion moment. It also covers admins and moderators, who never get
	   `completed_on` at all because completion tracking skips those roles.

	Only empty rows are touched, so this is safe to re-run and never overwrites a
	value that is already there.
	"""
	rows = get_documents_missing_submission_datetime()
	if not rows:
		print("backfill_document_submission_datetime: nothing to fill")
		return

	from_enrollment = from_last_lesson = 0

	for row in rows:
		stamp = row.certified_on or row.last_lesson_on
		if not stamp:
			continue

		frappe.db.set_value(
			"Employee Course Documents",
			row.docname,
			"submission_datetime",
			stamp,
			update_modified=False,
		)
		if row.certified_on:
			from_enrollment += 1
		else:
			from_last_lesson += 1

	filled = from_enrollment + from_last_lesson
	skipped = len(rows) - filled

	print(
		f"backfill_document_submission_datetime: filled {filled} of {len(rows)} empty record(s) "
		f"— {from_enrollment} from the enrollment's completed_on, "
		f"{from_last_lesson} from the last completed lesson"
	)

	if skipped:
		print(
			f"backfill_document_submission_datetime: {skipped} record(s) left empty — no "
			f"completion date and no completed lesson, so the course was never actually "
			f"finished. Review manually if a date is required for them."
		)


def get_documents_missing_submission_datetime():
	"""Empty employee documents, paired with both candidate completion dates.

	Either column comes back as None when no enrollment matches, when the learner
	never certified, or when no lesson was ever completed; the caller picks the
	first one present and counts the rest.
	"""
	return frappe.db.sql(
		"""
		SELECT
			ecd.name AS docname,
			le.completed_on AS certified_on,
			(
				SELECT MAX(cp.completed_on)
				FROM `tabLMS Course Progress` AS cp
				WHERE cp.enrollment = le.name
				  AND cp.completed_on IS NOT NULL
			) AS last_lesson_on
		FROM `tabEmployee Course Documents` AS ecd
		LEFT JOIN `tabEmployee` AS e
			ON e.name = ecd.employee
		LEFT JOIN `tabLMS Enrollment` AS le
			ON le.member = e.user_id
			AND le.course = ecd.course
			-- Older rows predate enrollment versioning and read as NULL on one
			-- side or the other; both mean the first cycle.
			AND COALESCE(le.enrollment_version, 1) = COALESCE(ecd.enrollment_version, 1)
		WHERE ecd.submission_datetime IS NULL
		""",
		as_dict=True,
	)

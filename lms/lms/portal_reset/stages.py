# Copyright (c) 2026, hybrowlabs and contributors
# For license information, please see license.txt
"""Batch-processing stages for a Portal Reset.

Every stage is **self-draining**: `pending_count()` only counts records that
still need processing, and `process_batch()` only touches records not yet
handled. That single property gives us three things for free:

* **Resumability** - after a crash/restart we just call the stages again; already
  processed rows are no longer "pending", so we continue from where we stopped
  without any stored cursor.
* **Idempotency** - re-running a batch is a no-op once the rows have been
  archived + reset.
* **Low memory** - we always fetch at most `limit` rows at a time.

Nothing is permanently deleted before it is archived: `archive_rows()` writes a
full JSON snapshot of every row into `Portal Reset Archive` first, and only then
is the live/active state cleared for the new cycle.
"""

import json

import frappe
from frappe.utils import now


def _json_default(value):
	# datetime / date / Decimal etc. -> str so the snapshot is always serialisable
	return str(value)


def archive_rows(job, course, reference_doctype, stage_key, rows, member_field="member"):
	"""Bulk-write JSON snapshots of `rows` into Portal Reset Archive.

	`rows` is a list of dicts (raw table rows). Uses a single multi-row INSERT to
	keep the archive write cheap even for large batches.
	"""
	if not rows:
		return 0

	stamp = now()
	values = []
	for row in rows:
		values.append((
			frappe.generate_hash(length=10),
			job,
			course,
			reference_doctype,
			row.get("name"),
			row.get(member_field),
			stage_key,
			stamp,
			json.dumps(row, default=_json_default),
			stamp,
			stamp,
			"Administrator",
			"Administrator",
		))

	frappe.db.bulk_insert(
		"Portal Reset Archive",
		fields=[
			"name", "job", "course", "reference_doctype", "reference_name", "member",
			"stage_key", "archived_on", "data", "creation", "modified", "owner", "modified_by",
		],
		values=values,
	)
	return len(values)


class BaseStage:
	key = ""
	label = ""

	def pending_count(self, course):
		raise NotImplementedError

	def process_batch(self, job, course, limit):
		"""Archive + reset up to `limit` records. Return (processed, last_record)."""
		raise NotImplementedError


class _ArchiveAndDeleteStage(BaseStage):
	"""Archive every row for the course, then remove it from the live table.

	Used for transient per-cycle state (course progress, quiz/assignment
	attempts). The data survives in Portal Reset Archive for audit/reporting.
	"""

	table = ""          # e.g. "LMS Course Progress"
	member_field = "member"

	def pending_count(self, course):
		return frappe.db.sql(
			f"SELECT COUNT(*) FROM `tab{self.table}` WHERE course = %s",
			course,
		)[0][0]

	def process_batch(self, job, course, limit):
		rows = frappe.db.sql(
			f"SELECT * FROM `tab{self.table}` WHERE course = %s ORDER BY name LIMIT %s",
			(course, limit),
			as_dict=True,
		)
		if not rows:
			return 0, None

		archive_rows(job, course, self.table, self.key, rows, self.member_field)

		names = [r["name"] for r in rows]
		placeholders = ", ".join(["%s"] * len(names))
		frappe.db.sql(
			f"DELETE FROM `tab{self.table}` WHERE name IN ({placeholders})",
			names,
		)
		return len(rows), names[-1]


class _ArchiveAndResetFlagStage(BaseStage):
	"""Archive rows whose submission flag is still set, then clear the flag.

	Uploaded files/records are preserved untouched - only the active submission
	state (`has_submitted_documents`) is reset so users must resubmit this cycle.
	"""

	table = ""
	member_field = "name"

	def pending_count(self, course):
		return frappe.db.sql(
			f"SELECT COUNT(*) FROM `tab{self.table}` "
			f"WHERE course = %s AND has_submitted_documents = 1",
			course,
		)[0][0]

	def process_batch(self, job, course, limit):
		rows = frappe.db.sql(
			f"SELECT * FROM `tab{self.table}` "
			f"WHERE course = %s AND has_submitted_documents = 1 ORDER BY name LIMIT %s",
			(course, limit),
			as_dict=True,
		)
		if not rows:
			return 0, None

		archive_rows(job, course, self.table, self.key, rows, self.member_field)

		names = [r["name"] for r in rows]
		placeholders = ", ".join(["%s"] * len(names))
		frappe.db.sql(
			f"UPDATE `tab{self.table}` SET has_submitted_documents = 0, modified = %s "
			f"WHERE name IN ({placeholders})",
			[now(), *names],
		)
		return len(rows), names[-1]


# --- Concrete transient-state stages -------------------------------------------------

class CourseProgressStage(_ArchiveAndDeleteStage):
	key = "course_progress"
	label = "Archive & Reset Course Progress"
	table = "LMS Course Progress"


class QuizSubmissionStage(_ArchiveAndDeleteStage):
	key = "quiz_submissions"
	label = "Archive Quiz Attempts"
	table = "LMS Quiz Submission"


class AssignmentSubmissionStage(_ArchiveAndDeleteStage):
	key = "assignment_submissions"
	label = "Archive Assignment Submissions"
	table = "LMS Assignment Submission"


# --- Compliance-document stages ------------------------------------------------------

class DistributorDocsStage(_ArchiveAndResetFlagStage):
	key = "distributor_documents"
	label = "Reset Distributor Compliance Documents"
	table = "Distributor Course Documents"


class EmployeeDocsStage(_ArchiveAndResetFlagStage):
	key = "employee_documents"
	label = "Reset Employee Compliance Documents"
	table = "Employee Course Documents"


# --- Enrollment stage ----------------------------------------------------------------

class EnrollmentStage(BaseStage):
	"""Reset each member's *latest* enrollment for the course.

	* A latest enrollment that is **Completed** gets a brand-new "Re-enrolled"
	  version (progress 0, access restored). History is preserved - the old row
	  stays as a Completed/access-restricted record, exactly like the interactive
	  re-enroll flow, minus the per-user email (never mass-mail a portal reset).
	* A latest enrollment that is still **active** but has progress simply has its
	  progress/certification cleared in place.

	"Pending" = a member whose latest enrollment is Completed OR has progress > 0.
	Once reset, the latest enrollment no longer matches, so the stage drains.
	"""

	key = "enrollments"
	label = "Reset Enrollments"

	_LATEST = """
		SELECT * FROM (
			SELECT e.*, ROW_NUMBER() OVER (
				PARTITION BY e.member
				ORDER BY e.enrollment_version DESC, e.creation DESC
			) AS rn
			FROM `tabLMS Enrollment` e
			WHERE e.course = %(course)s
		) t
		WHERE t.rn = 1 AND (t.completion_status = 'Completed' OR t.progress > 0)
	"""

	def pending_count(self, course):
		return frappe.db.sql(
			f"SELECT COUNT(*) FROM ({self._LATEST}) x",
			{"course": course},
		)[0][0]

	def process_batch(self, job, course, limit):
		rows = frappe.db.sql(
			f"{self._LATEST} ORDER BY t.member LIMIT %(limit)s",
			{"course": course, "limit": limit},
			as_dict=True,
		)
		if not rows:
			return 0, None

		# Snapshot the current latest state before we touch anything.
		archive_rows(job, course, "LMS Enrollment", self.key, rows, "member")

		completed = [r for r in rows if (r.get("completion_status") or "") == "Completed"]
		active = [r for r in rows if r not in completed]

		stamp = now()
		initiated_by = frappe.db.get_value("Portal Reset Job", job, "initiated_by") or "Administrator"

		# In-place reset for still-active enrollments with leftover progress.
		if active:
			names = [r["name"] for r in active]
			placeholders = ", ".join(["%s"] * len(names))
			frappe.db.sql(
				f"""
				UPDATE `tabLMS Enrollment`
				SET progress = 0, completed_on = NULL, current_lesson = NULL,
					course_reminder_count = 0, is_certified = 0, modified = %s
				WHERE name IN ({placeholders})
				""",
				[stamp, *names],
			)

		# Fresh re-enrollment version for completed enrollments.
		if completed:
			members = [r["member"] for r in completed]
			placeholders = ", ".join(["%s"] * len(members))
			agg = frappe.db.sql(
				f"""
				SELECT member, COUNT(*) AS cnt,
					MIN(creation) AS first_creation,
					MIN(original_enrollment_date) AS first_orig
				FROM `tabLMS Enrollment`
				WHERE course = %s AND member IN ({placeholders})
				GROUP BY member
				""",
				[course, *members],
				as_dict=True,
			)
			meta = {a["member"]: a for a in agg}

			new_rows = []
			for r in completed:
				m = meta.get(r["member"], {})
				total = m.get("cnt") or 1
				original_date = m.get("first_orig") or m.get("first_creation")
				new_rows.append((
					frappe.generate_hash(length=10),        # name
					r["member"], r.get("member_name"), course,
					r.get("member_type"), r.get("role"), r.get("batch_old"),
					r.get("cohort"), r.get("subgroup"),
					"Re-enrolled", 0, 0, None,               # status, access_restricted, progress, current_lesson
					initiated_by, stamp, original_date,
					total + 1, total, 0,                     # enrollment_version, re_enrollment_count, is_certified
					stamp, stamp, initiated_by, initiated_by, 0,
				))

			frappe.db.bulk_insert(
				"LMS Enrollment",
				fields=[
					"name", "member", "member_name", "course", "member_type", "role", "batch_old",
					"cohort", "subgroup", "completion_status", "access_restricted", "progress",
					"current_lesson", "re_enrolled_by", "re_enrolled_on", "original_enrollment_date",
					"enrollment_version", "re_enrollment_count", "is_certified",
					"creation", "modified", "owner", "modified_by", "docstatus",
				],
				values=new_rows,
			)

			# Mark the old completed rows as historical/access-restricted.
			old_names = [r["name"] for r in completed]
			placeholders = ", ".join(["%s"] * len(old_names))
			frappe.db.sql(
				f"""
				UPDATE `tabLMS Enrollment`
				SET access_restricted = 1,
					completed_on = COALESCE(completed_on, %s),
					modified = %s
				WHERE name IN ({placeholders})
				""",
				[stamp, stamp, *old_names],
			)

		return len(rows), rows[-1]["member"]


# Ordered pipeline. Transient per-cycle state is archived/cleared first, then the
# enrollments are reset last (so their fresh course-progress slate stays empty).
STAGES = [
	CourseProgressStage(),
	QuizSubmissionStage(),
	AssignmentSubmissionStage(),
	DistributorDocsStage(),
	EmployeeDocsStage(),
	EnrollmentStage(),
]


def get_stages():
	return STAGES

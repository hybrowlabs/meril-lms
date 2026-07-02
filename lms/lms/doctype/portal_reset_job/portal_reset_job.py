# Copyright (c) 2026, hybrowlabs and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now

from lms.lms.portal_reset.engine import run_job
from lms.lms.portal_reset.stages import get_stages

ACTIVE_STATUSES = ("Queued", "Running")
RESUMABLE_STATUSES = ("Failed", "Partially Completed", "Cancelled", "Queued", "Running")


class PortalResetJob(Document):
	def validate(self):
		if not self.batch_size or self.batch_size <= 0:
			self.batch_size = 200
		if self.is_new():
			self._guard_single_active_job()

	def before_insert(self):
		self.status = "Queued"
		self.initiated_by = frappe.session.user
		self.processed_records = 0
		self.progress_percentage = 0
		if not self.get("stages"):
			self._init_stages()

	def _guard_single_active_job(self):
		"""Only one active reset per course at a time."""
		existing = frappe.db.exists(
			"Portal Reset Job",
			{"course": self.course, "status": ["in", ACTIVE_STATUSES], "name": ["!=", self.name or ""]},
		)
		if existing:
			frappe.throw(
				_("A Portal Reset is already {0} for this course ({1}).").format(
					frappe.db.get_value("Portal Reset Job", existing, "status"), existing
				),
				title=_("Reset Already Running"),
			)

	def _init_stages(self):
		self.set("stages", [])
		for stage in get_stages():
			self.append("stages", {
				"stage_key": stage.key,
				"stage_label": stage.label,
				"status": "Pending",
				"total": 0,
				"processed": 0,
			})

	# --- lifecycle -----------------------------------------------------------------

	def enqueue(self):
		"""Enqueue the background worker on the `long` queue and record its id."""
		self._guard_single_active_job()
		frappe.db.set_value(self.doctype, self.name, "status", "Queued", update_modified=False)

		job = frappe.enqueue(
			run_job,
			queue="long",
			timeout=self._timeout(),
			job_id=self.background_job_id(),
			deduplicate=True,
			enqueue_after_commit=True,
			docname=self.name,
		)
		frappe.db.set_value(
			self.doctype, self.name, "rq_job_id", getattr(job, "id", None), update_modified=False
		)
		return job

	def background_job_id(self):
		return f"portal_reset::{self.name}"

	def _timeout(self):
		# generous ceiling; batches commit continuously so this rarely bites
		return 12 * 60 * 60

	def cancel_reset(self):
		if self.status not in ("Queued", "Running"):
			frappe.throw(_("Only a queued or running reset can be cancelled."))
		# The engine checks this flag between batches and stops gracefully.
		frappe.db.set_value(self.doctype, self.name, "status", "Cancelled", update_modified=False)
		frappe.db.set_value(self.doctype, self.name, "completed_on", now(), update_modified=False)
		frappe.db.commit()

	def resume(self):
		"""Re-enqueue a failed / cancelled / partially-completed job.

		Stages are self-draining, so resuming simply re-runs the pipeline and picks
		up whatever is still pending - no work is repeated.
		"""
		if self.status not in RESUMABLE_STATUSES:
			frappe.throw(_("This reset cannot be resumed (status: {0}).").format(self.status))
		frappe.db.set_value(self.doctype, self.name, {"status": "Queued", "completed_on": None}, update_modified=False)
		self.reload()
		return self.enqueue()


def enqueue_portal_reset(course, batch_size=200):
	"""Create a Portal Reset Job for `course` and enqueue it. Returns the job doc."""
	if not frappe.db.exists("LMS Course", course):
		frappe.throw(_("Course {0} not found.").format(course))

	job = frappe.new_doc("Portal Reset Job")
	job.course = course
	job.batch_size = batch_size or 200
	job.insert()
	job.enqueue()
	frappe.db.commit()
	return job

# Copyright (c) 2026, hybrowlabs and contributors
# For license information, please see license.txt
"""Whitelisted API for the Portal Reset feature (create / monitor / control)."""

import frappe
from frappe import _
from frappe.utils import cint

from lms.lms.doctype.portal_reset_job.portal_reset_job import enqueue_portal_reset

ALLOWED_ROLES = ("Administrator", "System Manager", "Supervisor")


def _guard():
	frappe.only_for(list(ALLOWED_ROLES))


@frappe.whitelist()
def start_portal_reset(course, batch_size=200):
	"""Create + enqueue a Portal Reset Job. Returns the job name for polling."""
	_guard()
	job = enqueue_portal_reset(course, cint(batch_size) or 200)
	return {"success": True, "job": job.name, "status": job.status}


@frappe.whitelist()
def get_portal_reset_job(job):
	"""Full status snapshot of a job (for the monitoring UI to poll)."""
	_guard()
	doc = frappe.get_doc("Portal Reset Job", job)
	return {
		"name": doc.name,
		"course": doc.course,
		"status": doc.status,
		"batch_size": doc.batch_size,
		"total_records": doc.total_records,
		"processed_records": doc.processed_records,
		"progress_percentage": doc.progress_percentage,
		"current_stage": doc.current_stage,
		"last_processed_record": doc.last_processed_record,
		"started_on": doc.started_on,
		"completed_on": doc.completed_on,
		"initiated_by": doc.initiated_by,
		"error_log": doc.error_log,
		"finished": doc.status in ("Completed", "Failed", "Cancelled", "Partially Completed"),
		"stages": [
			{
				"stage_key": s.stage_key,
				"stage_label": s.stage_label,
				"status": s.status,
				"total": s.total,
				"processed": s.processed,
				"error": s.error,
			}
			for s in doc.stages
		],
	}


@frappe.whitelist()
def get_active_reset_for_course(course):
	"""Return the latest active (Queued/Running) job for a course, if any."""
	_guard()
	job = frappe.db.get_value(
		"Portal Reset Job",
		{"course": course, "status": ["in", ("Queued", "Running")]},
		"name",
		order_by="creation desc",
	)
	return {"job": job} if job else {"job": None}


@frappe.whitelist()
def cancel_portal_reset(job):
	_guard()
	doc = frappe.get_doc("Portal Reset Job", job)
	doc.cancel_reset()
	return {"success": True, "status": "Cancelled"}


@frappe.whitelist()
def resume_portal_reset(job):
	"""Resume / retry a failed, cancelled or partially-completed job."""
	_guard()
	doc = frappe.get_doc("Portal Reset Job", job)
	doc.resume()
	return {"success": True, "status": doc.status}


@frappe.whitelist()
def list_portal_reset_jobs(course=None, limit=20):
	"""Recent jobs for the monitoring list."""
	_guard()
	filters = {}
	if course:
		filters["course"] = course
	return frappe.get_all(
		"Portal Reset Job",
		filters=filters,
		fields=[
			"name", "course", "status", "progress_percentage",
			"total_records", "processed_records", "current_stage",
			"started_on", "completed_on", "initiated_by", "creation",
		],
		order_by="creation desc",
		limit=cint(limit) or 20,
	)

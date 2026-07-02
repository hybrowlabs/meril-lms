# Copyright (c) 2026, hybrowlabs and contributors
# For license information, please see license.txt
"""Execution engine for a Portal Reset Job.

Runs the ordered stage pipeline in `stages.py`, committing after every batch so
that:

* lock duration is bounded to one batch,
* a crash/restart loses at most the in-flight batch (self-draining stages let us
  simply resume), and
* progress is visible in near real-time (each commit is followed by a realtime
  publish + DB update the monitoring UI polls).

The engine never loads the whole dataset into memory - stages fetch `batch_size`
rows at a time.
"""

import frappe
from frappe.utils import cint, now

from lms.lms.portal_reset.stages import get_stages

REALTIME_EVENT = "portal_reset_progress"
DEFAULT_BATCH_SIZE = 200
MIN_BATCH_SIZE = 50
MAX_BATCH_SIZE = 2000
# Consecutive batch failures within a stage before the whole job is failed.
MAX_BATCH_RETRIES = 3


def _publish(job_name, payload, user=None):
	payload = {"job": job_name, **payload}
	# Target the initiating admin's room so their SPA receives it regardless of the
	# worker's own session user.
	frappe.publish_realtime(REALTIME_EVENT, payload, user=user, after_commit=True)


def _set_stage(job_name, stage_key, **values):
	"""Update a single Portal Reset Job Stage child row by (parent, stage_key)."""
	if not values:
		return
	set_clause = ", ".join([f"`{k}` = %s" for k in values])
	frappe.db.sql(
		f"""
		UPDATE `tabPortal Reset Job Stage`
		SET {set_clause}
		WHERE parent = %s AND stage_key = %s
		""",
		[*values.values(), job_name, stage_key],
	)


def _job_is_cancelled(job_name):
	return frappe.db.get_value("Portal Reset Job", job_name, "status") == "Cancelled"


def _append_error(job_name, message):
	existing = frappe.db.get_value("Portal Reset Job", job_name, "error_log") or ""
	stamped = f"[{now()}] {message}"
	frappe.db.set_value(
		"Portal Reset Job",
		job_name,
		"error_log",
		(existing + "\n" + stamped).strip(),
		update_modified=False,
	)


def run_job(docname):
	"""Entry point invoked by the background worker (see api.enqueue_portal_reset)."""
	job_name = docname
	job = frappe.get_doc("Portal Reset Job", job_name)

	if job.status in ("Completed", "Cancelled"):
		return

	notify_user = job.initiated_by
	stages = get_stages()

	# (Re)compute the total once so progress % is stable across resumes.
	if not job.total_records:
		total = sum(stage.pending_count(job.course) for stage in stages)
		frappe.db.set_value("Portal Reset Job", job_name, "total_records", total, update_modified=False)
		job.total_records = total

	frappe.db.set_value(
		"Portal Reset Job",
		job_name,
		{"status": "Running", "started_on": job.started_on or now()},
		update_modified=False,
	)
	frappe.db.commit()
	_publish(job_name, {"status": "Running", "total": job.total_records}, user=notify_user)

	batch_size = min(max(cint(job.batch_size) or DEFAULT_BATCH_SIZE, MIN_BATCH_SIZE), MAX_BATCH_SIZE)
	processed_total = cint(job.processed_records)
	had_failure = False

	try:
		for stage in stages:
			if _job_is_cancelled(job_name):
				break

			frappe.db.set_value(
				"Portal Reset Job", job_name, "current_stage", stage.label, update_modified=False
			)
			pending = stage.pending_count(job.course)
			_set_stage(
				job_name, stage.key,
				status="Running", total=pending, stage_label=stage.label,
			)
			frappe.db.commit()

			stage_processed = 0
			retries = 0

			while True:
				if _job_is_cancelled(job_name):
					break

				try:
					count, last_record = stage.process_batch(job_name, job.course, batch_size)
				except Exception:
					frappe.db.rollback()
					retries += 1
					tb = frappe.get_traceback()
					frappe.log_error(tb, f"Portal Reset batch failed: {job_name}/{stage.key}")
					_append_error(job_name, f"{stage.key}: batch failed (attempt {retries}) - {tb.splitlines()[-1]}")
					frappe.db.commit()
					if retries >= MAX_BATCH_RETRIES:
						_set_stage(job_name, stage.key, status="Failed",
							error=f"Failed after {retries} attempts")
						frappe.db.commit()
						had_failure = True
						break
					continue

				if not count:
					break

				retries = 0
				stage_processed += count
				processed_total += count
				progress = min(100.0, (processed_total / job.total_records * 100.0) if job.total_records else 100.0)

				# One commit per batch - bounds lock time, enables resume.
				frappe.db.set_value(
					"Portal Reset Job", job_name,
					{
						"processed_records": processed_total,
						"progress_percentage": progress,
						"last_processed_record": str(last_record) if last_record else None,
					},
					update_modified=False,
				)
				_set_stage(job_name, stage.key, processed=stage_processed)
				frappe.db.commit()
				_publish(job_name, {
					"status": "Running",
					"stage": stage.label,
					"stage_key": stage.key,
					"processed": processed_total,
					"total": job.total_records,
					"progress": progress,
				}, user=notify_user)

			if not had_failure and not _job_is_cancelled(job_name):
				_set_stage(job_name, stage.key, status="Completed")
				frappe.db.commit()

		# --- finalise ------------------------------------------------------------
		if _job_is_cancelled(job_name):
			final_status = "Cancelled"
		elif had_failure:
			final_status = "Partially Completed"
		else:
			final_status = "Completed"

		frappe.db.set_value(
			"Portal Reset Job", job_name,
			{
				"status": final_status,
				"completed_on": now(),
				"current_stage": None,
				"progress_percentage": min(100.0, cint(processed_total) / job.total_records * 100.0)
					if job.total_records else 100.0,
			},
			update_modified=False,
		)
		frappe.db.commit()
		_publish(job_name, {"status": final_status, "processed": processed_total, "total": job.total_records}, user=notify_user)

	except Exception:
		frappe.db.rollback()
		tb = frappe.get_traceback()
		frappe.log_error(tb, f"Portal Reset Job crashed: {job_name}")
		_append_error(job_name, f"Fatal: {tb.splitlines()[-1]}")
		frappe.db.set_value(
			"Portal Reset Job", job_name,
			{"status": "Failed", "completed_on": now()},
			update_modified=False,
		)
		frappe.db.commit()
		_publish(job_name, {"status": "Failed"}, user=notify_user)
		raise

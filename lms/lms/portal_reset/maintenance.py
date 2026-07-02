# Copyright (c) 2026, hybrowlabs and contributors
# For license information, please see license.txt
"""Scheduled recovery for Portal Reset Jobs.

If a worker dies or the server restarts mid-reset, a job can be left in
`Queued`/`Running` with no live RQ job backing it. This scheduled task detects
those orphans and re-enqueues them. Because the stages are self-draining, the
resumed run continues from whatever is still pending - no work is repeated.
"""

import frappe
from frappe.utils.background_jobs import is_job_enqueued


def requeue_stuck_portal_resets():
	stuck = frappe.get_all(
		"Portal Reset Job",
		filters={"status": ["in", ("Queued", "Running")]},
		fields=["name"],
	)
	for row in stuck:
		job_id = f"portal_reset::{row.name}"
		# Still being worked on (queued or started)? leave it alone.
		if is_job_enqueued(job_id):
			continue
		try:
			doc = frappe.get_doc("Portal Reset Job", row.name)
			doc.add_comment("Comment", "Auto-recovered: worker was not running, re-enqueued.")
			doc.enqueue()
			frappe.db.commit()
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Portal Reset auto-recovery failed: {row.name}")
			frappe.db.rollback()

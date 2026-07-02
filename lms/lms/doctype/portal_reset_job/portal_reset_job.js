// Copyright (c) 2026, hybrowlabs and contributors
// For license information, please see license.txt

frappe.ui.form.on("Portal Reset Job", {
	refresh(frm) {
		frm.disable_save();
		render_progress(frm);
		add_buttons(frm);
		subscribe_realtime(frm);
	},

	onload(frm) {
		subscribe_realtime(frm);
	},
});

function add_buttons(frm) {
	frm.clear_custom_buttons();

	if (frm.is_new()) {
		return;
	}

	const status = frm.doc.status;

	if (["Failed", "Partially Completed", "Cancelled"].includes(status)) {
		frm.add_custom_button(__("Resume / Retry"), () => {
			frappe.call({
				method: "lms.lms.portal_reset.api.resume_portal_reset",
				args: { job: frm.doc.name },
				freeze: true,
				freeze_message: __("Resuming reset…"),
				callback: () => frm.reload_doc(),
			});
		}).addClass("btn-primary");
	}

	if (["Queued", "Running"].includes(status)) {
		frm.add_custom_button(__("Cancel Reset"), () => {
			frappe.confirm(__("Cancel this portal reset? It will stop after the current batch."), () => {
				frappe.call({
					method: "lms.lms.portal_reset.api.cancel_portal_reset",
					args: { job: frm.doc.name },
					freeze: true,
					callback: () => frm.reload_doc(),
				});
			});
		}).addClass("btn-danger");
	}

	frm.add_custom_button(__("View Archived Data"), () => {
		frappe.set_route("List", "Portal Reset Archive", { job: frm.doc.name });
	});
}

function render_progress(frm) {
	const d = frm.doc;
	const pct = Math.min(100, Math.round(d.progress_percentage || 0));
	const color = {
		Completed: "green",
		Running: "blue",
		Queued: "orange",
		Failed: "red",
		Cancelled: "gray",
		"Partially Completed": "orange",
	}[d.status] || "blue";

	const stages = (d.stages || [])
		.map((s) => {
			const badge = {
				Completed: "green",
				Running: "blue",
				Failed: "red",
				Skipped: "gray",
				Pending: "gray",
			}[s.status] || "gray";
			return `
				<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid var(--border-color);">
					<span>${frappe.utils.escape_html(s.stage_label || s.stage_key)}</span>
					<span>
						<span class="indicator-pill ${badge}">${s.status}</span>
						<span style="margin-left:8px;color:var(--text-muted);">${s.processed || 0} / ${s.total || 0}</span>
					</span>
				</div>`;
		})
		.join("");

	const html = `
		<div style="padding:12px 0;">
			<div style="display:flex;justify-content:space-between;margin-bottom:6px;">
				<b>${__("Status")}: <span class="indicator-pill ${color}">${d.status}</span></b>
				<span>${d.processed_records || 0} / ${d.total_records || 0} (${pct}%)</span>
			</div>
			<div style="background:var(--gray-200);border-radius:6px;height:12px;overflow:hidden;">
				<div style="width:${pct}%;height:12px;background:var(--${color}-500, #2490ef);transition:width .3s;"></div>
			</div>
			<div style="margin-top:6px;color:var(--text-muted);">${d.current_stage || ""}</div>
			<div style="margin-top:16px;">${stages}</div>
		</div>`;

	// The dashboard is cleared on every form refresh, so always render fresh.
	frm.dashboard.add_section(html, __("Reset Progress"));
}

function subscribe_realtime(frm) {
	if (frm.__prj_subscribed || frm.is_new()) {
		return;
	}
	frm.__prj_subscribed = true;
	frappe.realtime.on("portal_reset_progress", (data) => {
		if (!data || data.job !== frm.doc.name) {
			return;
		}
		// Light refresh: pull the latest doc so progress + stages update live.
		frm.reload_doc();
	});
}

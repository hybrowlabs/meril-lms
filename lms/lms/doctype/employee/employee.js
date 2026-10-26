// Copyright (c) 2025, Frappe and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee", {
	create_user(frm) {
		if (frm.is_new() || frm.is_dirty()) {
			frappe.msgprint(__("Please save the Employee before creating a User."));
			return;
		}

		const email = frm.doc.prefered_email || frm.doc.company_email || frm.doc.personal_email;
		if (!email) {
			frappe.msgprint(__("Please enter a Company Email, Personal Email or Preferred Email."));
			return;
		}

		// Same name split as erpnext.setup.doctype.employee.employee.create_user
		const parts = (frm.doc.employee_name || frm.doc.first_name || "").trim().split(/\s+/);
		let first_name = parts[0] || "";
		let middle_name = "";
		let last_name = "";
		if (parts.length >= 3) {
			middle_name = parts[1];
			last_name = parts.slice(2).join(" ");
		} else if (parts.length === 2) {
			last_name = parts[1];
		}

		const employee = frm.doc.name;

		frappe.route_options = {
			email: email,
			first_name: first_name,
			middle_name: middle_name,
			last_name: last_name,
			gender: frm.doc.gender,
			birth_date: frm.doc.date_of_birth,
			phone: frm.doc.cell_number,
			mobile_no: frm.doc.cell_number,
			send_welcome_email: 0,
		};

		// Runs once when the new User is saved: link it back to this Employee.
		frappe.route_hooks = frappe.route_hooks || {};
		frappe.route_hooks.after_save = (user_frm) => {
			frappe.db
				.set_value("Employee", employee, "user_id", user_frm.doc.name)
				.then(() => frappe.set_route("Form", "Employee", employee));
		};

		frappe.new_doc("User");
	},
});

// Copyright (c) 2026, Frappe and contributors
// For license information, please see license.txt

frappe.listview_settings["Distributor Course Documents"] = {
	onload: function (listview) {
		// Page-based Previous/Next pagination in the footer (matches the portal pages)
		frappe.lms.setup_list_pagination(listview, 20);
	},
};

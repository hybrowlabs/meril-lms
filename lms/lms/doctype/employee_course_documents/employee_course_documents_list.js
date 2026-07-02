// Copyright (c) 2026, Frappe and contributors
// For license information, please see license.txt

frappe.listview_settings["Employee Course Documents"] = {
	onload: function (listview) {
		// Page-based Previous/Next pagination at the top (no scrolling to a bottom "Load More")
		frappe.lms.setup_list_pagination(listview, 20);
	},
};

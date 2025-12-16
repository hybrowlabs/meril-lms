// Copyright (c) 2025
// Prevent auto-selection of company field during import

frappe.ui.form.on("Department", {
	onload: function(frm) {
		// Check if we're in import mode (indicated by __import flag or bulk import)
		const is_import_mode = frappe.flags.import_doc || 
			(frappe.route_options && frappe.route_options.import) ||
			window.location.href.includes('import');
		
		// For new documents, clear company field to prevent auto-selection
		if (frm.is_new() && !frm.doc.company) {
			// Ensure company field stays empty
			frm.set_value("company", "");
		}
		
		// During import, always clear company unless explicitly provided in data
		if (is_import_mode && frm.is_new() && !frm.doc._company_from_import) {
			frm.set_value("company", "");
		}
	},
	
	refresh: function(frm) {
		// Check if we're in import mode
		const is_import_mode = frappe.flags.import_doc || 
			(frappe.route_options && frappe.route_options.import) ||
			window.location.href.includes('import');
		
		// During import, ensure company field is empty unless data explicitly provides it
		if (is_import_mode && frm.is_new()) {
			// If company was auto-filled but not from import data, clear it
			if (frm.doc.company && !frm.doc._company_from_import) {
				frm.set_value("company", "");
			}
		}
	}
});


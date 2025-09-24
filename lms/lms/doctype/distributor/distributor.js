// Copyright (c) 2025, Frappe and contributors
// For license information, please see license.txt

frappe.ui.form.on("Distributor", {
	refresh(frm) {
		// Set up filters on form refresh
		setup_field_filters(frm);
	},

	onload(frm) {
		// Set up filters when form loads
		setup_field_filters(frm);
	},

	country(frm) {
		// When country changes, clear state and city
		if (frm.doc.country) {
			// Clear dependent fields
			frm.set_value('state', '');
			frm.set_value('city', '');

			// Set up the state filter
			frm.set_query('state', function() {
				return {
					filters: {
						'country': frm.doc.country
					}
				};
			});

			// Remove the restriction on city since state is now cleared
			setup_city_filter(frm);
		} else {
			// If country is cleared, clear state and city
			frm.set_value('state', '');
			frm.set_value('city', '');

			// Re-setup filters to show proper messages
			setup_field_filters(frm);
		}
	},

	state(frm) {
		// When state changes, clear city
		if (frm.doc.state) {
			// Clear dependent field
			frm.set_value('city', '');

			// Set up the city filter
			frm.set_query('city', function() {
				return {
					filters: {
						'state': frm.doc.state
					}
				};
			});
		} else {
			// If state is cleared, clear city
			frm.set_value('city', '');

			// Re-setup city filter to show proper message
			setup_city_filter(frm);
		}
	}
});

function setup_field_filters(frm) {
	// Set up state filter based on country selection
	setup_state_filter(frm);

	// Set up city filter based on state selection
	setup_city_filter(frm);
}

function setup_state_filter(frm) {
	if (frm.doc.country) {
		// If country is selected, filter states by that country
		frm.set_query('state', function() {
			return {
				filters: {
					'country': frm.doc.country
				}
			};
		});
	} else {
		// If no country is selected, prevent state selection and show message
		frm.set_query('state', function() {
			frappe.msgprint({
				title: __('Selection Required'),
				message: __('Please select a Country first'),
				indicator: 'orange'
			});
			return {
				filters: {
					'name': 'no-results-filter' // This ensures no results are shown
				}
			};
		});
	}
}

function setup_city_filter(frm) {
	if (!frm.doc.country) {
		// If no country is selected, prevent city selection
		frm.set_query('city', function() {
			frappe.msgprint({
				title: __('Selection Required'),
				message: __('Please select a Country first'),
				indicator: 'orange'
			});
			return {
				filters: {
					'name': 'no-results-filter' // This ensures no results are shown
				}
			};
		});
	} else if (!frm.doc.state) {
		// If country is selected but no state, show different message
		frm.set_query('city', function() {
			frappe.msgprint({
				title: __('Selection Required'),
				message: __('Please select a State first'),
				indicator: 'orange'
			});
			return {
				filters: {
					'name': 'no-results-filter' // This ensures no results are shown
				}
			};
		});
	} else {
		// Both country and state are selected, filter cities by state
		frm.set_query('city', function() {
			return {
				filters: {
					'state': frm.doc.state
				}
			};
		});
	}
}

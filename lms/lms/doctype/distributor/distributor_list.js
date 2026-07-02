// Copyright (c) 2025, Frappe and contributors
// For license information, please see license.txt

frappe.listview_settings['Distributor'] = {
	add_fields: ["user_id", "is_active_user", "distributor_email_address"],
	get_indicator: function(doc) {
		if (doc.user_id) {
			return [__("User Created"), "green", "user_id,=," + doc.user_id];
		} else {
			return [__("No User"), "red", "user_id,is,not set"];
		}
	},
	onload: function(listview) {
		// Page-based Previous/Next pagination at the top (no scrolling to a bottom "Load More")
		frappe.lms.setup_list_pagination(listview, 20);

		// Add custom button as an inner button (more prominent)
		listview.page.add_inner_button(__("Send Email"), function() {
			open_bulk_user_creation_dialog(listview);
		});
		// Add Resend Email button
		listview.page.add_inner_button(__("Resend Email"), function() {
			open_bulk_resend_email_dialog(listview);
		});

		// Actions menu - Direct Send Email (no dialog)
		listview.page.add_actions_menu_item(__("Send Email"), function() {
			send_email_to_selected_distributors(listview);
		}, false);

		// Actions menu - Direct Resend Email (no dialog)
		listview.page.add_actions_menu_item(__("Resend Email"), function() {
			resend_email_to_selected_distributors(listview);
		}, false);
	}
};

// Direct action function for Actions menu - Send Email (no dialog)
function send_email_to_selected_distributors(listview) {
	let selected = listview.get_checked_items(true);
	if (!selected.length) {
		frappe.msgprint(__('Please select at least one distributor'));
		return;
	}

	frappe.confirm(
		__('Create users and send emails for {0} selected distributors?', [selected.length]),
		function() {
			process_bulk_user_creation(selected, {});
		}
	);
}

// Direct action function for Actions menu - Resend Email (no dialog)
function resend_email_to_selected_distributors(listview) {
	let selected = listview.get_checked_items(true);
	if (!selected.length) {
		frappe.msgprint(__('Please select at least one distributor'));
		return;
	}

	frappe.confirm(
		__('Resend initial email to {0} selected distributors?', [selected.length]),
		function() {
			process_bulk_resend_emails(selected, {});
		}
	);
}

function open_bulk_user_creation_dialog(listview) {
	// Check if rows are pre-selected in list view
	let pre_selected = listview.get_checked_items(true);

	let dialog = new frappe.ui.Dialog({
		title: __('Create Users & Send Emails'),
		fields: [
			{
				fieldtype: 'Section Break',
				label: __('Filter Distributors')
			},
			{
				fieldname: 'division',
				fieldtype: 'Link',
				label: __('Division'),
				options: 'Division'
			},
			{
				fieldname: 'country',
				fieldtype: 'Link',
				label: __('Country'),
				options: 'Country'
			},
			{
				fieldname: 'state',
				fieldtype: 'Link',
				label: __('State'),
				options: 'State'
			},
			{
				fieldname: 'city',
				fieldtype: 'Link',
				label: __('City'),
				options: 'City'
			},
			{
				fieldname: 'distributor_company_name',
				fieldtype: 'Data',
				label: __('Company Name')
			},
			{
				fieldname: 'bu__fd_head',
				fieldtype: 'Data',
				label: __('BU / FD Head')
			},
			{
				fieldname: 'rsm__state_head',
				fieldtype: 'Data',
				label: __('RSM / State Head')
			},
			{
				fieldtype: 'Column Break'
			},
			{
				fieldname: 'attendee_name',
				fieldtype: 'Data',
				label: __('Attendee Name')
			},
			{
				fieldname: 'distributor_name',
				fieldtype: 'Data',
				label: __('Distributor Name')
			},
			{
				fieldname: 'region',
				fieldtype: 'Data',
				label: __('Region')
			},
			{
				fieldname: 'only_without_users',
				fieldtype: 'Check',
				label: __('Only Distributors Without Users'),
				default: 1,
				description: __('Show only distributors who don\'t have user accounts yet')
			},
			{
				fieldtype: 'Section Break',
				label: __('Search Results')
			},
			{
				fieldname: 'distributors_html',
				fieldtype: 'HTML',
				label: __('Distributors')
			}
		],
		primary_action_label: __('Create Users & Send Emails'),
		primary_action: function() {
			let selected_distributors = get_selected_distributors_from_dialog(dialog);
			if (selected_distributors.length === 0) {
				frappe.msgprint(__('Please select at least one distributor'));
				return;
			}

			let filters = get_dialog_filters(dialog);

			frappe.confirm(
				__('Create user accounts and send login credentials for {0} selected distributors?', [selected_distributors.length]),
				function() {
					dialog.hide();
					process_bulk_user_creation(selected_distributors, filters);
				}
			);
		},
		secondary_action_label: __('Search'),
		secondary_action: function() {
			// Clear pre-selection when user manually searches
			dialog.pre_selected_ids = null;
			load_distributors_in_dialog(dialog);
		}
	});

	// Store pre-selected IDs in dialog for use in load function
	dialog.pre_selected_ids = pre_selected.length > 0 ? pre_selected : null;

	// Set up field dependencies
	setup_dialog_field_dependencies(dialog);

	// Initial load with pre-selected filter if any
	load_distributors_in_dialog(dialog);

	dialog.show();
}

function setup_dialog_field_dependencies(dialog) {
	// Country -> State dependency
	dialog.fields_dict.country.df.onchange = function() {
		if (dialog.get_value('country')) {
			dialog.set_value('state', '');
			dialog.set_value('city', '');

			dialog.fields_dict.state.get_query = function() {
				return {
					filters: {
						'country': dialog.get_value('country')
					}
				};
			};
		}
		load_distributors_in_dialog(dialog);
	};

	// State -> City dependency
	dialog.fields_dict.state.df.onchange = function() {
		if (dialog.get_value('state')) {
			dialog.set_value('city', '');

			dialog.fields_dict.city.get_query = function() {
				return {
					filters: {
						'state': dialog.get_value('state')
					}
				};
			};
		}
		load_distributors_in_dialog(dialog);
	};

	// Other field changes
	['division', 'city', 'distributor_company_name', 'bu__fd_head', 'rsm__state_head',
	 'attendee_name', 'distributor_name', 'region', 'only_without_users'].forEach(function(field) {
		dialog.fields_dict[field].df.onchange = function() {
			load_distributors_in_dialog(dialog);
		};
	});
}

function get_dialog_filters(dialog) {
	let filters = {};

	// Link fields use exact match
	['division', 'country', 'state', 'city'].forEach(function(field) {
		let value = dialog.get_value(field);
		if (value) {
			filters[field] = value;
		}
	});

	// Data fields use "like" operator for partial matching
	['distributor_company_name', 'bu__fd_head', 'rsm__state_head', 'attendee_name', 'distributor_name', 'region'].forEach(function(field) {
		let value = dialog.get_value(field);
		if (value) {
			filters[field] = ['like', '%' + value + '%'];
		}
	});

	if (dialog.get_value('only_without_users')) {
		filters['user_id'] = ['is', 'not set'];
	}

	return filters;
}

function load_distributors_in_dialog(dialog) {
	let filters = get_dialog_filters(dialog);

	// If pre-selected IDs exist, filter by them
	if (dialog.pre_selected_ids && dialog.pre_selected_ids.length > 0) {
		filters['name'] = ['in', dialog.pre_selected_ids];
	}

	// Also need to join with child table for division filter
	let method = 'frappe.client.get_list';
	let args = {
		doctype: 'Distributor',
		filters: filters,
		fields: ['name', 'attendee_name', 'distributor_name', 'distributor_email_address',
				 'distributor_company_name', 'country', 'state', 'city', 'user_id', 'is_active_user'],
		limit_page_length: 0,
		order_by: 'creation desc'
	};

	// If division filter is applied, we need to use a custom method
	if (filters.division) {
		method = 'lms.lms.user.get_distributors_by_division';
		args = {
			division: filters.division,
			filters: filters
		};
	}

	frappe.call({
		method: method,
		args: args,
		callback: function(r) {
			if (r.message) {
				display_distributors_in_dialog(dialog, r.message);
			}
		}
	});
}

function display_distributors_in_dialog(dialog, distributors) {
	let html = `
		<div style="max-height: 300px; overflow-y: auto;">
			<table class="table table-bordered">
				<thead>
					<tr>
						<th style="width: 30px;">
							<input type="checkbox" id="select_all_distributors" class="select-all-checkbox">
						</th>
						<th>Name</th>
						<th>Email</th>
						<th>Company</th>
						<th>Location</th>
						<th>Status</th>
					</tr>
				</thead>
				<tbody>
	`;

	distributors.forEach(function(distributor) {
		let name = distributor.attendee_name || distributor.distributor_name || 'N/A';
		let location = [distributor.city, distributor.state, distributor.country].filter(Boolean).join(', ') || 'N/A';
		let status = distributor.user_id ?
			'<span class="indicator green">User Created</span>' :
			'<span class="indicator red">No User</span>';

		html += `
			<tr>
				<td>
					<input type="checkbox" class="distributor-checkbox" value="${frappe.utils.escape_html(distributor.name)}"
						   ${!distributor.user_id ? 'checked' : ''}>
				</td>
				<td>${frappe.utils.escape_html(name)}</td>
				<td>${frappe.utils.escape_html(distributor.distributor_email_address || 'N/A')}</td>
				<td>${frappe.utils.escape_html(distributor.distributor_company_name || 'N/A')}</td>
				<td>${frappe.utils.escape_html(location)}</td>
				<td>${status}</td>
			</tr>
		`;
	});

	html += `
				</tbody>
			</table>
		</div>
		<p class="text-muted">Found ${distributors.length} distributors</p>
	`;

	dialog.fields_dict.distributors_html.$wrapper.html(html);
	
	// Attach event listeners using event delegation
	setup_checkbox_handlers(dialog);
}

function setup_checkbox_handlers(dialog) {
	let $wrapper = dialog.fields_dict.distributors_html.$wrapper;
	
	// Remove any existing handlers to prevent duplicates
	$wrapper.off('change', '.select-all-checkbox');
	$wrapper.off('change', '.distributor-checkbox');
	
	// Handle select all checkbox - use class selector to work with both dialogs
	$wrapper.on('change', '.select-all-checkbox', function() {
		let is_checked = $(this).is(':checked');
		$wrapper.find('.distributor-checkbox').prop('checked', is_checked);
	});
	
	// Handle individual checkbox changes to update select all state
	$wrapper.on('change', '.distributor-checkbox', function() {
		let total_checkboxes = $wrapper.find('.distributor-checkbox').length;
		let checked_checkboxes = $wrapper.find('.distributor-checkbox:checked').length;
		$wrapper.find('.select-all-checkbox').prop('checked', total_checkboxes === checked_checkboxes);
	});
	
	// Initialize select all checkbox state
	let total_checkboxes = $wrapper.find('.distributor-checkbox').length;
	let checked_checkboxes = $wrapper.find('.distributor-checkbox:checked').length;
	$wrapper.find('.select-all-checkbox').prop('checked', total_checkboxes > 0 && total_checkboxes === checked_checkboxes);
}

function get_selected_distributors_from_dialog(dialog) {
	let selected = [];
	let $wrapper = dialog ? dialog.fields_dict.distributors_html.$wrapper : $('.distributors_html');
	$wrapper.find('.distributor-checkbox:checked').each(function() {
		selected.push($(this).val());
	});
	return selected;
}

function open_bulk_resend_email_dialog(listview) {
	// Check if rows are pre-selected in list view
	let pre_selected = listview.get_checked_items(true);

	let dialog = new frappe.ui.Dialog({
		title: __('Resend Initial Email'),
		fields: [
			{
				fieldtype: 'Section Break',
				label: __('Filter Distributors')
			},
			{
				fieldname: 'division',
				fieldtype: 'Link',
				label: __('Division'),
				options: 'Division'
			},
			{
				fieldname: 'country',
				fieldtype: 'Link',
				label: __('Country'),
				options: 'Country'
			},
			{
				fieldname: 'state',
				fieldtype: 'Link',
				label: __('State'),
				options: 'State'
			},
			{
				fieldname: 'city',
				fieldtype: 'Link',
				label: __('City'),
				options: 'City'
			},
			{
				fieldname: 'distributor_company_name',
				fieldtype: 'Data',
				label: __('Company Name')
			},
			{
				fieldname: 'bu__fd_head',
				fieldtype: 'Data',
				label: __('BU / FD Head')
			},
			{
				fieldname: 'rsm__state_head',
				fieldtype: 'Data',
				label: __('RSM / State Head')
			},
			{
				fieldtype: 'Column Break'
			},
			{
				fieldname: 'attendee_name',
				fieldtype: 'Data',
				label: __('Attendee Name')
			},
			{
				fieldname: 'distributor_name',
				fieldtype: 'Data',
				label: __('Distributor Name')
			},
			{
				fieldname: 'region',
				fieldtype: 'Data',
				label: __('Region')
			},
			{
				fieldname: 'only_with_users',
				fieldtype: 'Check',
				label: __('Only Distributors With Users'),
				default: 1,
				description: __('Show only distributors who have user accounts')
			},
			{
				fieldtype: 'Section Break',
				label: __('Search Results')
			},
			{
				fieldname: 'distributors_html',
				fieldtype: 'HTML',
				label: __('Distributors')
			}
		],
		primary_action_label: __('Resend Emails'),
		primary_action: function() {
			let selected_distributors = get_selected_distributors_from_dialog(dialog);
			if (selected_distributors.length === 0) {
				frappe.msgprint(__('Please select at least one distributor'));
				return;
			}

			let filters = get_resend_dialog_filters(dialog);

			frappe.confirm(
				__('Resend initial email to {0} selected distributors?', [selected_distributors.length]),
				function() {
					dialog.hide();
					process_bulk_resend_emails(selected_distributors, filters);
				}
			);
		},
		secondary_action_label: __('Search'),
		secondary_action: function() {
			// Clear pre-selection when user manually searches
			dialog.pre_selected_ids = null;
			load_distributors_in_resend_dialog(dialog);
		}
	});

	// Store pre-selected IDs in dialog for use in load function
	dialog.pre_selected_ids = pre_selected.length > 0 ? pre_selected : null;

	// Set up field dependencies
	setup_resend_dialog_field_dependencies(dialog);

	// Initial load with pre-selected filter if any
	load_distributors_in_resend_dialog(dialog);

	dialog.show();
}

function setup_resend_dialog_field_dependencies(dialog) {
	// Country -> State dependency
	dialog.fields_dict.country.df.onchange = function() {
		if (dialog.get_value('country')) {
			dialog.set_value('state', '');
			dialog.set_value('city', '');

			dialog.fields_dict.state.get_query = function() {
				return {
					filters: {
						'country': dialog.get_value('country')
					}
				};
			};
		}
		load_distributors_in_resend_dialog(dialog);
	};

	// State -> City dependency
	dialog.fields_dict.state.df.onchange = function() {
		if (dialog.get_value('state')) {
			dialog.set_value('city', '');

			dialog.fields_dict.city.get_query = function() {
				return {
					filters: {
						'state': dialog.get_value('state')
					}
				};
			};
		}
		load_distributors_in_resend_dialog(dialog);
	};

	// Other field changes
	['division', 'city', 'distributor_company_name', 'bu__fd_head', 'rsm__state_head',
	 'attendee_name', 'distributor_name', 'region', 'only_with_users'].forEach(function(field) {
		dialog.fields_dict[field].df.onchange = function() {
			load_distributors_in_resend_dialog(dialog);
		};
	});
}

function get_resend_dialog_filters(dialog) {
	let filters = {};

	// Link fields use exact match
	['division', 'country', 'state', 'city'].forEach(function(field) {
		let value = dialog.get_value(field);
		if (value) {
			filters[field] = value;
		}
	});

	// Data fields use "like" operator for partial matching
	['distributor_company_name', 'bu__fd_head', 'rsm__state_head', 'attendee_name', 'distributor_name', 'region'].forEach(function(field) {
		let value = dialog.get_value(field);
		if (value) {
			filters[field] = ['like', '%' + value + '%'];
		}
	});

	if (dialog.get_value('only_with_users')) {
		filters['user_id'] = ['is', 'set'];
	}

	return filters;
}

function load_distributors_in_resend_dialog(dialog) {
	let filters = get_resend_dialog_filters(dialog);

	// If pre-selected IDs exist, filter by them
	if (dialog.pre_selected_ids && dialog.pre_selected_ids.length > 0) {
		filters['name'] = ['in', dialog.pre_selected_ids];
	}

	// Also need to join with child table for division filter
	let method = 'frappe.client.get_list';
	let args = {
		doctype: 'Distributor',
		filters: filters,
		fields: ['name', 'attendee_name', 'distributor_name', 'distributor_email_address',
				 'distributor_company_name', 'country', 'state', 'city', 'user_id', 'is_active_user'],
		limit_page_length: 0,
		order_by: 'creation desc'
	};

	// If division filter is applied, we need to use a custom method
	if (filters.division) {
		method = 'lms.lms.user.get_distributors_by_division';
		args = {
			division: filters.division,
			filters: filters
		};
	}

	frappe.call({
		method: method,
		args: args,
		callback: function(r) {
			if (r.message) {
				display_distributors_in_resend_dialog(dialog, r.message);
			}
		}
	});
}

function display_distributors_in_resend_dialog(dialog, distributors) {
	let html = `
		<div style="max-height: 300px; overflow-y: auto;">
			<table class="table table-bordered">
				<thead>
					<tr>
						<th style="width: 30px;">
							<input type="checkbox" id="select_all_distributors_resend" class="select-all-checkbox">
						</th>
						<th>Name</th>
						<th>Email</th>
						<th>Company</th>
						<th>Location</th>
						<th>Status</th>
					</tr>
				</thead>
				<tbody>
	`;

	distributors.forEach(function(distributor) {
		let name = distributor.attendee_name || distributor.distributor_name || 'N/A';
		let location = [distributor.city, distributor.state, distributor.country].filter(Boolean).join(', ') || 'N/A';
		let status = distributor.user_id ?
			'<span class="indicator green">User Created</span>' :
			'<span class="indicator red">No User</span>';

		html += `
			<tr>
				<td>
					<input type="checkbox" class="distributor-checkbox" value="${frappe.utils.escape_html(distributor.name)}"
						   ${distributor.user_id ? 'checked' : ''}>
				</td>
				<td>${frappe.utils.escape_html(name)}</td>
				<td>${frappe.utils.escape_html(distributor.distributor_email_address || 'N/A')}</td>
				<td>${frappe.utils.escape_html(distributor.distributor_company_name || 'N/A')}</td>
				<td>${frappe.utils.escape_html(location)}</td>
				<td>${status}</td>
			</tr>
		`;
	});

	html += `
				</tbody>
			</table>
		</div>
		<p class="text-muted">Found ${distributors.length} distributors</p>
	`;

	dialog.fields_dict.distributors_html.$wrapper.html(html);
	
	// Attach event listeners using event delegation
	setup_checkbox_handlers(dialog);
}

function process_bulk_user_creation(distributor_ids, filters) {
	frappe.show_progress(__('Creating Users'), 0, distributor_ids.length, __('Starting...'));

	frappe.call({
		method: 'lms.lms.user.bulk_create_users_from_distributors',
		args: {
			distributor_ids: distributor_ids,
			filters: filters
		},
		callback: function(r) {
			frappe.hide_progress();

			if (r.message) {
				let results = r.message;
				let success_count = results.success.length;
				let error_count = results.errors.length;
				let exists_count = results.already_exists.length;

				let message = `
					<div>
						<h4>Bulk User Creation Results</h4>
						<p><strong>✅ Successfully Created:</strong> ${success_count}</p>
						<p><strong>⚠️ Already Existed:</strong> ${exists_count}</p>
						<p><strong>❌ Errors:</strong> ${error_count}</p>
					</div>
				`;

				if (error_count > 0) {
					message += '<div><h5>Errors:</h5><ul>';
					results.errors.forEach(function(error) {
						message += `<li>${error.name}: ${error.error}</li>`;
					});
					message += '</ul></div>';
				}

				frappe.msgprint({
					title: __('Bulk User Creation Complete'),
					message: message,
					indicator: success_count > 0 ? 'green' : (error_count > 0 ? 'red' : 'orange')
				});

				// Refresh the list view
				if (window.cur_list) {
					window.cur_list.refresh();
				}
			}
		},
		error: function(r) {
			frappe.hide_progress();
			frappe.msgprint(__('An error occurred during bulk user creation. Please check the error logs.'));
		}
	});
}

function process_bulk_resend_emails(distributor_ids, filters) {
	frappe.show_progress(__('Resending Emails'), 0, distributor_ids.length, __('Starting...'));

	frappe.call({
		method: 'lms.lms.user.bulk_resend_emails_to_distributors',
		args: {
			distributor_ids: distributor_ids,
			filters: filters
		},
		callback: function(r) {
			frappe.hide_progress();

			if (r.message) {
				let results = r.message;
				let success_count = results.success.length;
				let error_count = results.errors.length;
				let skipped_count = results.skipped.length;

				let message = `
					<div>
						<h4>Bulk Email Resend Results</h4>
						<p><strong>✅ Successfully Sent:</strong> ${success_count}</p>
						<p><strong>⚠️ Skipped:</strong> ${skipped_count}</p>
						<p><strong>❌ Errors:</strong> ${error_count}</p>
					</div>
				`;

				if (skipped_count > 0) {
					message += '<div><h5>Skipped:</h5><ul>';
					results.skipped.forEach(function(item) {
						message += `<li>${item.name}: ${item.message}</li>`;
					});
					message += '</ul></div>';
				}

				if (error_count > 0) {
					message += '<div><h5>Errors:</h5><ul>';
					results.errors.forEach(function(error) {
						message += `<li>${error.name}: ${error.error}</li>`;
					});
					message += '</ul></div>';
				}

				frappe.msgprint({
					title: __('Bulk Email Resend Complete'),
					message: message,
					indicator: success_count > 0 ? 'green' : (error_count > 0 ? 'red' : 'orange')
				});

				// Refresh the list view
				if (window.cur_list) {
					window.cur_list.refresh();
				}
			}
		},
		error: function(r) {
			frappe.hide_progress();
			frappe.msgprint(__('An error occurred during bulk email resend. Please check the error logs.'));
		}
	});
}
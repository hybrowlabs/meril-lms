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
		// Add custom button as an inner button (more prominent)
		listview.page.add_inner_button(__("Send Email"), function() {
			open_bulk_user_creation_dialog(listview);
		});
	}
};

function open_bulk_user_creation_dialog(listview) {
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
			let selected_distributors = get_selected_distributors_from_dialog();
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
			load_distributors_in_dialog(dialog);
		}
	});

	// Set up field dependencies
	setup_dialog_field_dependencies(dialog);

	// Initial load
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

	['division', 'country', 'state', 'city', 'distributor_company_name',
	 'bu__fd_head', 'rsm__state_head', 'attendee_name', 'distributor_name', 'region'].forEach(function(field) {
		let value = dialog.get_value(field);
		if (value) {
			filters[field] = value;
		}
	});

	if (dialog.get_value('only_without_users')) {
		filters['user_id'] = ['is', 'not set'];
	}

	return filters;
}

function load_distributors_in_dialog(dialog) {
	let filters = get_dialog_filters(dialog);

	// Also need to join with child table for division filter
	let method = 'frappe.client.get_list';
	let args = {
		doctype: 'Distributor',
		filters: filters,
		fields: ['name', 'attendee_name', 'distributor_name', 'distributor_email_address',
				 'distributor_company_name', 'country', 'state', 'city', 'user_id', 'is_active_user'],
		limit_page_length: 100,
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
							<input type="checkbox" id="select_all_distributors" onchange="toggle_all_distributors(this)">
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
					<input type="checkbox" class="distributor-checkbox" value="${distributor.name}"
						   ${!distributor.user_id ? 'checked' : ''}>
				</td>
				<td>${name}</td>
				<td>${distributor.distributor_email_address || 'N/A'}</td>
				<td>${distributor.distributor_company_name || 'N/A'}</td>
				<td>${location}</td>
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
}

function toggle_all_distributors(checkbox) {
	let checkboxes = document.querySelectorAll('.distributor-checkbox');
	checkboxes.forEach(function(cb) {
		cb.checked = checkbox.checked;
	});
}

function get_selected_distributors_from_dialog() {
	let selected = [];
	let checkboxes = document.querySelectorAll('.distributor-checkbox:checked');
	checkboxes.forEach(function(cb) {
		selected.push(cb.value);
	});
	return selected;
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
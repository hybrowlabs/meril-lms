// Copyright (c) 2025, Frappe and contributors
// For license information, please see license.txt

frappe.listview_settings['Employee'] = {
	add_fields: ["user_id", "company_email"],
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
		// Add Resend Email button
		listview.page.add_inner_button(__("Resend Email"), function() {
			open_bulk_resend_email_dialog(listview);
		});
	}
};

function open_bulk_user_creation_dialog(listview) {
	let dialog = new frappe.ui.Dialog({
		title: __('Create Users & Send Emails'),
		fields: [
			{
				fieldtype: 'Section Break',
				label: __('Filter Employees')
			},
			{
				fieldname: 'company',
				fieldtype: 'Link',
				label: __('Company'),
				options: 'Company'
			},
			{
				fieldname: 'department',
				fieldtype: 'Link',
				label: __('Department'),
				options: 'Department'
			},
			{
				fieldname: 'designation',
				fieldtype: 'Link',
				label: __('Designation'),
				options: 'Designation'
			},
			{
				fieldname: 'custom_country',
				fieldtype: 'Link',
				label: __('Country'),
				options: 'Country'
			},
			{
				fieldtype: 'Column Break'
			},
			{
				fieldname: 'first_name',
				fieldtype: 'Data',
				label: __('First Name')
			},
			{
				fieldname: 'last_name',
				fieldtype: 'Data',
				label: __('Last Name')
			},
			{
				fieldname: 'only_without_users',
				fieldtype: 'Check',
				label: __('Only Employees Without Users'),
				default: 1,
				description: __('Show only employees who don\'t have user accounts yet')
			},
			{
				fieldtype: 'Section Break',
				label: __('Search Results')
			},
			{
				fieldname: 'employees_html',
				fieldtype: 'HTML',
				label: __('Employees')
			}
		],
		primary_action_label: __('Create Users & Send Emails'),
		primary_action: function() {
			let selected_employees = get_selected_employees_from_dialog(dialog);
			if (selected_employees.length === 0) {
				frappe.msgprint(__('Please select at least one employee'));
				return;
			}

			let filters = get_dialog_filters(dialog);

			frappe.confirm(
				__('Create user accounts and send login credentials for {0} selected employees?', [selected_employees.length]),
				function() {
					dialog.hide();
					process_bulk_employee_user_creation(selected_employees, filters);
				}
			);
		},
		secondary_action_label: __('Search'),
		secondary_action: function() {
			load_employees_in_dialog(dialog);
		}
	});

	// Set up field dependencies
	setup_dialog_field_dependencies(dialog);

	// Initial load
	load_employees_in_dialog(dialog);

	dialog.show();
}

function setup_dialog_field_dependencies(dialog) {
	// Company -> Department dependency
	dialog.fields_dict.company.df.onchange = function() {
		if (dialog.get_value('company')) {
			dialog.set_value('department', '');

			dialog.fields_dict.department.get_query = function() {
				return {
					filters: {
						'company': dialog.get_value('company')
					}
				};
			};
		}
		load_employees_in_dialog(dialog);
	};

	// Other field changes
	['department', 'designation', 'custom_country', 'first_name', 'last_name', 'only_without_users'].forEach(function(field) {
		dialog.fields_dict[field].df.onchange = function() {
			load_employees_in_dialog(dialog);
		};
	});
}

function get_dialog_filters(dialog) {
	let filters = {};

	// Link fields use exact match
	['company', 'department', 'designation', 'custom_country'].forEach(function(field) {
		let value = dialog.get_value(field);
		if (value) {
			filters[field] = value;
		}
	});

	// Data fields use "like" operator for partial matching
	['first_name', 'last_name'].forEach(function(field) {
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

function load_employees_in_dialog(dialog) {
	let filters = get_dialog_filters(dialog);

	frappe.call({
		method: 'frappe.client.get_list',
		args: {
			doctype: 'Employee',
			filters: filters,
			fields: ['name', 'first_name', 'last_name', 'company_email', 'company', 'department', 'designation', 'custom_country', 'user_id'],
			limit_page_length: 100,
			order_by: 'creation desc'
		},
		callback: function(r) {
			if (r.message) {
				display_employees_in_dialog(dialog, r.message);
			}
		}
	});
}

function display_employees_in_dialog(dialog, employees) {
	let html = `
		<div style="max-height: 300px; overflow-y: auto;">
			<table class="table table-bordered">
				<thead>
					<tr>
						<th style="width: 30px;">
							<input type="checkbox" id="select_all_employees" class="select-all-checkbox">
						</th>
						<th>Name</th>
						<th>Email</th>
						<th>Company</th>
						<th>Department</th>
						<th>Country</th>
						<th>Status</th>
					</tr>
				</thead>
				<tbody>
	`;

	employees.forEach(function(employee) {
		let full_name = [employee.first_name, employee.last_name].filter(Boolean).join(' ') || 'N/A';
		let status = employee.user_id ?
			'<span class="indicator green">User Created</span>' :
			'<span class="indicator red">No User</span>';

		html += `
			<tr>
				<td>
					<input type="checkbox" class="employee-checkbox" value="${frappe.utils.escape_html(employee.name)}"
						   ${!employee.user_id ? 'checked' : ''}>
				</td>
				<td>${frappe.utils.escape_html(full_name)}</td>
				<td>${frappe.utils.escape_html(employee.company_email || 'N/A')}</td>
				<td>${frappe.utils.escape_html(employee.company || 'N/A')}</td>
				<td>${frappe.utils.escape_html(employee.department || 'N/A')}</td>
				<td>${frappe.utils.escape_html(employee.custom_country || 'N/A')}</td>
				<td>${status}</td>
			</tr>
		`;
	});

	html += `
				</tbody>
			</table>
		</div>
		<p class="text-muted">Found ${employees.length} employees</p>
	`;

	dialog.fields_dict.employees_html.$wrapper.html(html);
	
	// Setup checkbox handlers
	setup_checkbox_handlers_send(dialog);
}

function setup_checkbox_handlers_send(dialog) {
	let $wrapper = dialog.fields_dict.employees_html.$wrapper;
	
	// Remove any existing handlers to prevent duplicates
	$wrapper.off('change', '.select-all-checkbox');
	$wrapper.off('change', '.employee-checkbox');
	
	// Handle select all checkbox
	$wrapper.on('change', '#select_all_employees', function() {
		let is_checked = $(this).is(':checked');
		$wrapper.find('.employee-checkbox').prop('checked', is_checked);
	});
	
	// Handle individual checkbox changes to update select all state
	$wrapper.on('change', '.employee-checkbox', function() {
		let total_checkboxes = $wrapper.find('.employee-checkbox').length;
		let checked_checkboxes = $wrapper.find('.employee-checkbox:checked').length;
		$wrapper.find('#select_all_employees').prop('checked', total_checkboxes === checked_checkboxes);
	});
	
	// Initialize select all checkbox state
	let total_checkboxes = $wrapper.find('.employee-checkbox').length;
	let checked_checkboxes = $wrapper.find('.employee-checkbox:checked').length;
	$wrapper.find('#select_all_employees').prop('checked', total_checkboxes > 0 && total_checkboxes === checked_checkboxes);
}

function get_selected_employees_from_dialog(dialog) {
	let selected = [];
	let $wrapper = dialog ? dialog.fields_dict.employees_html.$wrapper : $('.employees_html');
	$wrapper.find('.employee-checkbox:checked').each(function() {
		selected.push($(this).val());
	});
	return selected;
}

function set_user_country(employee) {
	if (!employee || !employee.company_email || !employee.custom_country) {
		return;
	}

	frappe.call({
		method: 'frappe.client.set_value',
		args: {
			doctype: 'User',
			name: employee.company_email,
			fieldname: 'country',
			value: employee.custom_country
		}
	});
}

function process_bulk_employee_user_creation(employee_ids, filters) {
	frappe.show_progress(__('Creating Users'), 0, employee_ids.length, __('Starting...'));

	// Process employees one by one using the existing create_user_from_employee function
	let processed = 0;
	let results = {
		success: [],
		errors: [],
		already_exists: [],
		total: employee_ids.length
	};

	function process_next_employee() {
		if (processed >= employee_ids.length) {
			// All done, show results
			frappe.hide_progress();
			show_bulk_creation_results(results);
			return;
		}

		let employee_id = employee_ids[processed];
		processed++;

		frappe.call({
			method: 'lms.lms.user.create_user_from_employee',
			args: {
				employee_id: employee_id,
				_method: 'manual'  // Pass manual to bypass automatic creation check
			},
			callback: function(r) {
				// Get employee details for result display
				frappe.call({
					method: 'frappe.client.get',
					args: {
						doctype: 'Employee',
						name: employee_id,
						fields: ['first_name', 'last_name', 'company_email', 'custom_country']
					},
					callback: function(emp_r) {
						let employee = emp_r.message;
						let name = [employee.first_name, employee.last_name].filter(Boolean).join(' ');

						set_user_country(employee);

						results.success.push({
							employee_id: employee_id,
							name: name,
							email: employee.company_email,
							message: "User created and email sent successfully"
						});

						frappe.show_progress(__('Creating Users'), processed, employee_ids.length,
							__('Processing {0}...', [name]));

						// Process next employee after a short delay
						setTimeout(process_next_employee, 500);
					}
				});
			},
			error: function(r) {
				frappe.call({
					method: 'frappe.client.get',
					args: {
						doctype: 'Employee',
						name: employee_id,
						fields: ['first_name', 'last_name', 'company_email', 'custom_country']
					},
					callback: function(emp_r) {
						let employee = emp_r.message || {};
						let name = [employee.first_name, employee.last_name].filter(Boolean).join(' ') || employee_id;

						set_user_country(employee);

						// Check if it's because user already exists
						if (r.message && r.message.includes('already exists')) {
							results.already_exists.push({
								employee_id: employee_id,
								name: name,
								email: employee.company_email,
								message: "User already exists"
							});
						} else {
							results.errors.push({
								employee_id: employee_id,
								name: name,
								error: r.message || 'Unknown error'
							});
						}

						frappe.show_progress(__('Creating Users'), processed, employee_ids.length,
							__('Processing {0}...', [name]));

						// Process next employee after a short delay
						setTimeout(process_next_employee, 500);
					}
				});
			}
		});
	}

	// Start processing
	process_next_employee();
}

function show_bulk_creation_results(results) {
	let success_count = results.success.length;
	let error_count = results.errors.length;
	let exists_count = results.already_exists.length;

	let message = `
		<div>
			<h4>Bulk Employee User Creation Results</h4>
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
		title: __('Bulk Employee User Creation Complete'),
		message: message,
		indicator: success_count > 0 ? 'green' : (error_count > 0 ? 'red' : 'orange')
	});

	// Refresh the list view
	if (window.cur_list) {
		window.cur_list.refresh();
	}
}

function open_bulk_resend_email_dialog(listview) {
	let dialog = new frappe.ui.Dialog({
		title: __('Resend Initial Email'),
		fields: [
			{
				fieldtype: 'Section Break',
				label: __('Filter Employees')
			},
			{
				fieldname: 'company',
				fieldtype: 'Link',
				label: __('Company'),
				options: 'Company'
			},
			{
				fieldname: 'department',
				fieldtype: 'Link',
				label: __('Department'),
				options: 'Department'
			},
			{
				fieldname: 'designation',
				fieldtype: 'Link',
				label: __('Designation'),
				options: 'Designation'
			},
			{
				fieldname: 'custom_country',
				fieldtype: 'Link',
				label: __('Country'),
				options: 'Country'
			},
			{
				fieldtype: 'Column Break'
			},
			{
				fieldname: 'first_name',
				fieldtype: 'Data',
				label: __('First Name')
			},
			{
				fieldname: 'last_name',
				fieldtype: 'Data',
				label: __('Last Name')
			},
			{
				fieldname: 'only_with_users',
				fieldtype: 'Check',
				label: __('Only Employees With Users'),
				default: 1,
				description: __('Show only employees who have user accounts')
			},
			{
				fieldtype: 'Section Break',
				label: __('Search Results')
			},
			{
				fieldname: 'employees_html',
				fieldtype: 'HTML',
				label: __('Employees')
			}
		],
		primary_action_label: __('Resend Emails'),
		primary_action: function() {
			let selected_employees = get_selected_employees_from_resend_dialog(dialog);
			if (selected_employees.length === 0) {
				frappe.msgprint(__('Please select at least one employee'));
				return;
			}

			let filters = get_resend_dialog_filters_employee(dialog);

			frappe.confirm(
				__('Resend initial email to {0} selected employees?', [selected_employees.length]),
				function() {
					dialog.hide();
					process_bulk_resend_emails_employee(selected_employees, filters);
				}
			);
		},
		secondary_action_label: __('Search'),
		secondary_action: function() {
			load_employees_in_resend_dialog(dialog);
		}
	});

	// Set up field dependencies
	setup_resend_dialog_field_dependencies_employee(dialog);

	// Initial load
	load_employees_in_resend_dialog(dialog);

	dialog.show();
}

function setup_resend_dialog_field_dependencies_employee(dialog) {
	// Company -> Department dependency
	dialog.fields_dict.company.df.onchange = function() {
		if (dialog.get_value('company')) {
			dialog.set_value('department', '');

			dialog.fields_dict.department.get_query = function() {
				return {
					filters: {
						'company': dialog.get_value('company')
					}
				};
			};
		}
		load_employees_in_resend_dialog(dialog);
	};

	// Other field changes
	['department', 'designation', 'custom_country', 'first_name', 'last_name', 'only_with_users'].forEach(function(field) {
		dialog.fields_dict[field].df.onchange = function() {
			load_employees_in_resend_dialog(dialog);
		};
	});
}

function get_resend_dialog_filters_employee(dialog) {
	let filters = {};

	// Link fields use exact match
	['company', 'department', 'designation', 'custom_country'].forEach(function(field) {
		let value = dialog.get_value(field);
		if (value) {
			filters[field] = value;
		}
	});

	// Data fields use "like" operator for partial matching
	['first_name', 'last_name'].forEach(function(field) {
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

function load_employees_in_resend_dialog(dialog) {
	let filters = get_resend_dialog_filters_employee(dialog);

	frappe.call({
		method: 'frappe.client.get_list',
		args: {
			doctype: 'Employee',
			filters: filters,
			fields: ['name', 'first_name', 'last_name', 'company_email', 'company', 'department', 'designation', 'custom_country', 'user_id'],
			limit_page_length: 100,
			order_by: 'creation desc'
		},
		callback: function(r) {
			if (r.message) {
				display_employees_in_resend_dialog(dialog, r.message);
			}
		}
	});
}

function display_employees_in_resend_dialog(dialog, employees) {
	let html = `
		<div style="max-height: 300px; overflow-y: auto;">
			<table class="table table-bordered">
				<thead>
					<tr>
						<th style="width: 30px;">
							<input type="checkbox" id="select_all_employees_resend" class="select-all-checkbox">
						</th>
						<th>Name</th>
						<th>Email</th>
						<th>Company</th>
						<th>Department</th>
						<th>Country</th>
						<th>Status</th>
					</tr>
				</thead>
				<tbody>
	`;

	employees.forEach(function(employee) {
		let full_name = [employee.first_name, employee.last_name].filter(Boolean).join(' ') || 'N/A';
		let status = employee.user_id ?
			'<span class="indicator green">User Created</span>' :
			'<span class="indicator red">No User</span>';

		html += `
			<tr>
				<td>
					<input type="checkbox" class="employee-checkbox-resend" value="${frappe.utils.escape_html(employee.name)}"
						   ${employee.user_id ? 'checked' : ''}>
				</td>
				<td>${frappe.utils.escape_html(full_name)}</td>
				<td>${frappe.utils.escape_html(employee.company_email || 'N/A')}</td>
				<td>${frappe.utils.escape_html(employee.company || 'N/A')}</td>
				<td>${frappe.utils.escape_html(employee.department || 'N/A')}</td>
				<td>${frappe.utils.escape_html(employee.custom_country || 'N/A')}</td>
				<td>${status}</td>
			</tr>
		`;
	});

	html += `
				</tbody>
			</table>
		</div>
		<p class="text-muted">Found ${employees.length} employees</p>
	`;

	dialog.fields_dict.employees_html.$wrapper.html(html);
	
	// Setup checkbox handlers
	setup_checkbox_handlers_employee(dialog);
}

function setup_checkbox_handlers_employee(dialog) {
	// Select all checkbox
	let selectAllCheckbox = dialog.fields_dict.employees_html.$wrapper.find('#select_all_employees_resend');
	if (selectAllCheckbox.length) {
		selectAllCheckbox.off('change').on('change', function() {
			let isChecked = $(this).is(':checked');
			dialog.fields_dict.employees_html.$wrapper.find('.employee-checkbox-resend').prop('checked', isChecked);
		});
	}

	// Individual checkboxes
	dialog.fields_dict.employees_html.$wrapper.find('.employee-checkbox-resend').off('change').on('change', function() {
		let allChecked = dialog.fields_dict.employees_html.$wrapper.find('.employee-checkbox-resend:checked').length === 
						dialog.fields_dict.employees_html.$wrapper.find('.employee-checkbox-resend').length;
		selectAllCheckbox.prop('checked', allChecked);
	});
}

function get_selected_employees_from_resend_dialog(dialog) {
	let selected = [];
	dialog.fields_dict.employees_html.$wrapper.find('.employee-checkbox-resend:checked').each(function() {
		selected.push($(this).val());
	});
	return selected;
}

function process_bulk_resend_emails_employee(employee_ids, filters) {
	frappe.show_progress(__('Resending Emails'), 0, employee_ids.length, __('Starting...'));

	frappe.call({
		method: 'lms.lms.user.bulk_resend_emails_to_employees',
		args: {
			employee_ids: employee_ids,
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
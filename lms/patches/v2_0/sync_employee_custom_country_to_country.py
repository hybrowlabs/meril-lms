import frappe


def execute():
	"""Copy Employee.custom_country into the standard Employee.country field.

	Every lookup used to read `custom_country` first and fall back to `country`,
	so wherever `custom_country` is set it is the value the app was acting on.
	The app now reads only `country`; `custom_country` stays as a hidden field
	that `sync_employee_country` keeps copying across.
	"""
	if not frappe.db.has_column("Employee", "custom_country"):
		return

	frappe.db.sql(
		"""
		UPDATE `tabEmployee`
		SET country = custom_country
		WHERE IFNULL(custom_country, '') != ''
			AND IFNULL(country, '') != custom_country
		"""
	)

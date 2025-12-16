# Copyright (c) 2025
# License: GNU General Public License v3. See license.txt

import frappe
from frappe import _
from frappe.model.naming import set_name_by_naming_series

# Try to import HRMS EmployeeMaster, fallback to ERPNext Employee if HRMS not available
try:
	from hrms.hrms.overrides.employee_master import EmployeeMaster
	BASE_CLASS = EmployeeMaster
	HAS_HRMS = True
except ImportError:
	from erpnext.setup.doctype.employee.employee import Employee
	BASE_CLASS = Employee
	HAS_HRMS = False


class CustomEmployeeMaster(BASE_CLASS):
	"""
	Override Employee autoname to use custom_employee_id instead of standard naming
	"""
	def autoname(self):
		# Use custom_employee_id if provided
		if self.custom_employee_id:
			# Validate uniqueness
			if frappe.db.exists("Employee", {"custom_employee_id": self.custom_employee_id, "name": ("!=", self.name)}):
				frappe.throw(_("Employee ID {0} already exists").format(self.custom_employee_id))
			self.name = self.custom_employee_id
			self.employee = self.name
		else:
			# Fall back to parent class naming if custom_employee_id is not set
			if HAS_HRMS:
				super().autoname()
			else:
				# ERPNext Employee autoname
				set_name_by_naming_series(self)
				self.employee = self.name


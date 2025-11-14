# Copyright (c) 2025
# License: GNU General Public License v3. See license.txt

import frappe
from erpnext.setup.doctype.department.department import Department


class CustomDepartment(Department):
	"""
	Override Department to make company field non-mandatory
	This is handled via property setter, but we keep this class for consistency
	"""
	pass


# Copyright (c) 2025
# License: GNU General Public License v3. See license.txt

import frappe
from erpnext.setup.doctype.department.department import Department


class CustomDepartment(Department):
	"""
	Override Department to make company field non-mandatory and prevent auto-selection
	"""
	def validate(self):
		# Ensure company field can be empty (non-mandatory)
		# This is already handled by property setter, but we ensure it here too
		super().validate()
	
	def before_insert(self):
		# During import, if company is not explicitly set, keep it empty
		# This prevents any auto-selection logic from filling it
		if not hasattr(self, '_company_explicitly_set') and not self.company:
			# Explicitly set to None/empty to prevent any defaults
			self.company = None


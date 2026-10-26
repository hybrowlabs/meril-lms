# Copyright (c) 2025, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class Distributor(Document):
	"""Named ``{distributor_name}({distributor_email_address})`` (see autoname in
	distributor.json). The email is the login (``user_id``) and every backend lookup
	resolves a distributor by it, so one record per email is enforced here. A
	distributor working with several Meril companies is one record with one
	``meril_company_table`` row per company, each carrying its own code."""

	def before_insert(self):
		self.normalise_identity()

	def validate(self):
		self.normalise_identity()
		self.validate_unique_email()
		self.validate_company_rows()
		self.sync_account_code()

	def normalise_identity(self):
		self.distributor_name = (self.distributor_name or "").strip()
		self.distributor_email_address = (self.distributor_email_address or "").strip().lower()

	def validate_unique_email(self):
		filters = {"distributor_email_address": self.distributor_email_address}
		if not self.is_new():
			filters["name"] = ("!=", self.name)
		other = frappe.db.get_value("Distributor", filters, "name")
		if other:
			frappe.throw(
				_("Distributor {0} already uses the email {1}").format(
					frappe.bold(other), frappe.bold(self.distributor_email_address)
				),
				title=_("Duplicate Email"),
			)

	def validate_company_rows(self):
		seen = set()
		for row in self.meril_company_table:
			if not row.meril_company_name or not row.distributor_code:
				frappe.throw(
					_("Row #{0}: Meril Company and Distributor Code are both required").format(row.idx),
					title=_("Meril Company Table"),
				)
			row.distributor_code = row.distributor_code.strip()
			key = (row.meril_company_name, row.distributor_code.lower())
			if key in seen:
				frappe.throw(
					_("Row #{0}: code {1} is repeated for {2}").format(
						row.idx, frappe.bold(row.distributor_code), frappe.bold(row.meril_company_name)
					),
					title=_("Meril Company Table"),
				)
			seen.add(key)

			filters = {
				"parenttype": "Distributor",
				"meril_company_name": row.meril_company_name,
				"distributor_code": row.distributor_code,
			}
			if not self.is_new():
				filters["parent"] = ("!=", self.name)
			other = frappe.db.get_value("Meril Distributor Division Child", filters, "parent")
			if other:
				frappe.throw(
					_("Row #{0}: code {1} for {2} is already assigned to Distributor {3}").format(
						row.idx,
						frappe.bold(row.distributor_code),
						frappe.bold(row.meril_company_name),
						frappe.bold(other),
					),
					title=_("Meril Company Table"),
				)

	def sync_account_code(self):
		"""Reports and dashboards fall back to the parent code; keep it equal to the
		first company row so a single-company distributor reads the same everywhere."""
		self.account__distributor_code = (
			self.meril_company_table[0].distributor_code if self.meril_company_table else None
		)

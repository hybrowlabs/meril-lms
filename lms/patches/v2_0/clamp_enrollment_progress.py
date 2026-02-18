import frappe


def execute():
	"""Cap all LMS Enrollment progress values to 100."""
	frappe.db.sql("""
		UPDATE `tabLMS Enrollment`
		SET progress = 100
		WHERE progress > 100
	""")
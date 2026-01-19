import frappe

@frappe.whitelist()
def get_default_project_warehouse():
	"""Return the default project warehouse from STEMS Settings."""
	return frappe.db.get_single_value(
		"STEMS Settings",
		"default_project_warehouse"
	)

import frappe

@frappe.whitelist()
def get_site_engineers(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql("""
		SELECT name, employee_name
		FROM `tabEmployee`
		WHERE name IN (
			SELECT parent
			FROM `tabHas Role`
			WHERE role = 'Site Engineer'
		)
		AND {key} LIKE %s
		ORDER BY name
		LIMIT %s, %s
	""".format(key=searchfield), ("%%%s%%" % txt, start, page_len))

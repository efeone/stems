# Copyright (c) 2025, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils.user import get_users_with_role

class CustomerNeedProfile(Document):
	pass

@frappe.whitelist()
def make_customer_need_profile(source_name, target_doc=None):
	"""
		Create a Customer Need Profile from an Opportunity
	"""
	def set_missing_values(source, target):
		target.posting_date = frappe.utils.nowdate()

	doc = get_mapped_doc(
		"Opportunity",
		source_name,
		{
			"Opportunity": {
				"doctype": "Customer Need Profile",
				"field_map": {
					"name": "enquiry",
					"party_name": "lead",
					"customer_name": "customer_name",
					"contact_email": "customer_email",
					"phone": "customer_phone",
					"site_visit_required": "site_visit_required",
					"drawing_required": "drawing_required",
					"site_visit_scheduled_on": "site_visit_scheduled_on",
					"site_engineer": "site_engineer_supervisor"
				},
			},
			"Opportunity Item": {
				"doctype": "Customer Need Profile Item",
				"field_map": {
					"item_code": "item",
					"qty": "qty",
					"uom": "uom",
					"description": "description"
				}
			}
		},
		target_doc,
		set_missing_values
	)

	return doc

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_site_engineers(doctype, txt, searchfield, start, page_len, filters):
	"""
	Fetch employees linked to users with the 'Site Engineer' role
	for Link field searches.
	"""
	users = get_users_with_role("Site Engineer")
	if not users:
		return []

	employees = frappe.get_all(
		"Employee",
		filters={
			"user_id": ["in", users],
			searchfield: ["like", f"%{txt}%"]
		},
		fields=["name", "employee_name"],
		start=start,
		page_length=page_len
	)

	return [(d.name, d.employee_name) for d in employees]

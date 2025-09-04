# Copyright (c) 2025, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc


class BillofQuantity(Document):
	pass


@frappe.whitelist()
def make_quotation(source_name, target_doc=None):
	"""Map BOQ to Quotation with custom item rules"""

	def set_missing_values(source, target):

		target.quotation_to = "Lead"
		target.party_name = source.lead
		target.customer_name = frappe.db.get_value("Lead", source.lead, "lead_name")

		if source.customer_need_profile:
			cnp = frappe.get_doc("Customer Need Profile", source.customer_need_profile)

			if cnp.billing_type == "Items and Service" and cnp.customer_provided_items:
				for item in source.items:
					target.append("items", {
						"item_code": item.item,
						"item_name": item.item_name,
						"qty": item.qty,
						"uom": item.uom
					})

		for item in source.items:
			target.append("required_items", {
				"item_code": item.item,
				"item_name": item.item_name,
				"qty": item.qty,
				"uom": item.uom
			})

	doc = get_mapped_doc(
		"Bill of Quantity",
		source_name,
		{
			"Bill of Quantity": {
				"doctype": "Quotation",
				"field_map": {
					"lead": "party",
					"customer_name": "customer_name",
					"customer_need_profile": "customer_need_profile"
				}
			}
		},
		target_doc,
		set_missing_values
	)

	return doc

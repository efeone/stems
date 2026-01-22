# Copyright (c) 2025, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import today


class BillofQuantity(Document):
	pass

@frappe.whitelist()
def make_quotation(source_name, target_doc=None):
	"""Create Quotation from BOQ with custom item rules"""

	def postprocess(source, target):
		target.quotation_to = "Lead"
		target.party_name = source.lead
		target.customer_name = frappe.db.get_value("Lead", source.lead, "lead_name")
		target.customer_need_profile = source.customer_need_profile
		target.bill_of_quantity = source.name
		target.items = []
		target.required_items = []

		for row in source.items:
			row_data = {
				"item_code": row.item,
				"item_name": row.item_name,
				"qty": row.qty,
				"uom": row.uom,
				"customer_provided": row.customer_provided,
				"description": row.description,
			}
			if row.customer_provided:
				target.append("required_items", row_data)
			else:
				target.append("items", row_data)

	doc = get_mapped_doc(
		"Bill of Quantity",
		source_name,
		{
			"Bill of Quantity": {
				"doctype": "Quotation"
			}
		},
		target_doc,
		postprocess=postprocess
	)
	return doc

@frappe.whitelist()
def get_item_stock_balance(item):
	"""
	Fetch the stock balance (actual quantity) of a given item in its default warehouse.
	"""
	if not item:
		return 0
	item_default = frappe.get_value("Item Default",{"parent":item},["company","default_warehouse"], as_dict = True)
	if not item_default or not item_default.default_warehouse:
		return 0
	warehouse = item_default.default_warehouse
	actual_qty = frappe.get_value("Bin",{"item_code":item , "warehouse":warehouse},"actual_qty") or 0
	return actual_qty 

@frappe.whitelist()
def create_rfq_from_boq(source_name):
	"""
		Create Request for Quotation from Bill of Quantity considering stock levels
	"""
	boq = frappe.get_doc("Bill of Quantity", source_name)

	rfq = frappe.new_doc("Request for Quotation")
	rfq.bill_of_quantity = boq.name
	rfq.transaction_date = frappe.utils.today()
	rfq.schedule_date = frappe.utils.today()

	for row in boq.items:
		if not row.item or not row.qty:
			continue

		if row.customer_provided:
			continue

		stock_uom = frappe.get_value("Item", row.item, "stock_uom")

		default_warehouse = frappe.get_value(
			"Item Default",
			{"parent": row.item},
			"default_warehouse"
		)

		if not default_warehouse:
			frappe.throw(f"Default warehouse not set for Item {row.item}")

		available_qty = get_item_stock_balance(row.item)
		shortage_qty = max(row.qty - available_qty, 0)

		if shortage_qty > 0:
			rfq.append("items", {
				"item_code": row.item,
				"qty": shortage_qty,
				"uom": row.uom,
				"stock_uom": stock_uom,
				"conversion_factor": 1,
				"warehouse": default_warehouse,
				"description": row.description
			})

	rfq.insert(ignore_permissions=True, ignore_mandatory=True)
	return rfq.name


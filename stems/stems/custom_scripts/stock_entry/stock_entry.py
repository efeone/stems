# Copyright (c) 2025, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt
from frappe import _

def validate_stock_entry_qty(doc, method):
	"""
		Validate that the quantity being transferred does not exceed the required quantity in BOQ.
	"""
	if doc.stock_entry_type != "Material Transfer":
		return

	for item in doc.items:
		boq_item = frappe.db.get_value(
			"Bill of Quantity Item",
			{"item": item.item_code},
			["qty", "transferred_quantity"],
			order_by="modified desc",
			as_dict=True
		)

		if not boq_item:
			continue

		required_qty = flt(boq_item.qty) - flt(boq_item.transferred_quantity or 0)

		if item.qty > required_qty:
			frappe.throw(
				_("Cannot transfer more than required quantity for item {0}. Required: {1}")
				.format(item.item_code, required_qty)
			)

def update_boq_transferred_qty(doc, method):
	"""
		Update the transferred quantity in BOQ items after Stock Entry submission.
	"""
	if doc.stock_entry_type != "Material Transfer":
		return

	for item in doc.items:
		frappe.db.sql("""
			UPDATE `tabBill of Quantity Item`
			SET transferred_quantity = IFNULL(transferred_quantity, 0) + %s
			WHERE item = %s
		""", (item.qty, item.item_code))


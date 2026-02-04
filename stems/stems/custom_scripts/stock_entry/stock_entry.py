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
	Update transferred qty in BOQ, but do NOT allow exceeding qty.
	"""
	if doc.stock_entry_type != "Material Transfer":
		return

	for item in doc.items:
		boq_item = frappe.db.get_value(
			"Bill of Quantity Item",
			{"item": item.item_code},
			["name", "qty", "transferred_quantity"],
			as_dict=True
		)

		if not boq_item:
			continue

		existing = boq_item.transferred_quantity or 0
		new_total = existing + item.qty

		if new_total > boq_item.qty:
			new_total = boq_item.qty

		frappe.db.set_value(
			"Bill of Quantity Item",
			boq_item.name,
			"transferred_quantity",
			new_total
		)

def freeze_stock_balance_when_completed(doc, method):
	"""
	Freeze stock_balance only when transferred_quantity == qty.
	Material Receipt should not modify stock_balance.
	"""
	if doc.stock_entry_type != "Material Transfer":
		return

	for item in doc.items:
		boq_item = frappe.db.get_value(
			"Bill of Quantity Item",
			{"item": item.item_code},
			["name", "qty", "transferred_quantity", "stock_balance"],
			as_dict=True
		)

		if not boq_item:
			continue

		if boq_item.transferred_quantity == boq_item.qty:
			current_stock = frappe.db.get_value(
				"Bin",
				{"item_code": item.item_code, "warehouse": item.s_warehouse},
				"actual_qty"
			) or 0

			new_balance = current_stock

			frappe.db.set_value(
				"Bill of Quantity Item",
				boq_item.name,
				"stock_balance",
				new_balance
			)

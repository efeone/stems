"""
Percentage-based invoicing for Sales Order.
Service items: percentage on amount (rate adjusted). Stock items: percentage on qty.
Supports one percentage for the order or per-item percentage in the popup.
"""

import frappe
from frappe import _
from frappe.utils import flt
from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice


def _get_billed_qty_and_amount(sales_order_name, so_detail):
	""" Returns the total billed quantity and amount for a given sales order item detail."""
	result = frappe.db.sql(
		"""
		SELECT SUM(sii.qty), SUM(sii.amount)
		FROM `tabSales Invoice Item` sii
		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
		WHERE sii.sales_order = %s AND sii.so_detail = %s AND si.docstatus = 1
		""",
		(sales_order_name, so_detail),
	)
	if not result or not result[0]:
		return 0, 0
	return flt(result[0][0]), flt(result[0][1])


def update_so_item_invoiced_amounts(sales_invoice, method=None):
	""" Updates the invoiced and remaining amounts for sales order items linked to the given sales invoice."""
	if sales_invoice.docstatus not in (1, 2):
		return
	so_items = [
		(item.get("sales_order"), item.get("so_detail"))
		for item in (sales_invoice.items or [])
		if item.get("sales_order") and item.get("so_detail")
	]
	if not so_items:
		return
	so_to_details = {}
	for so_name, so_detail in so_items:
		so_to_details.setdefault(so_name, set()).add(so_detail)
	for so_name, so_details in so_to_details.items():
		for so_detail in so_details:
			invoiced = frappe.db.sql(
				"""
				SELECT SUM(sii.amount)
				FROM `tabSales Invoice Item` sii
				INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
				WHERE sii.sales_order = %s AND sii.so_detail = %s AND si.docstatus = 1
				""",
				(so_name, so_detail),
			)
			invoiced_amt = flt(invoiced[0][0] if invoiced and invoiced[0] else 0)
			so_item = frappe.db.get_value(
				"Sales Order Item",
				so_detail,
				["qty", "rate", "parent"],
				as_dict=True,
			)
			if not so_item:
				continue
			total_amt = flt(so_item.qty) * flt(so_item.rate)
			remaining_amt = max(0, total_amt - invoiced_amt)
			frappe.db.set_value(
				"Sales Order Item",
				so_detail,
				{"invoiced_amount": invoiced_amt, "remaining_amount": remaining_amt},
			)
	frappe.db.commit()


def set_initial_so_item_amounts(sales_order, method=None):
	""" Initializes the invoiced and remaining amounts for sales order items when a sales order is submitted."""
	if sales_order.docstatus != 1:
		return
	for row in sales_order.items:
		total_amt = flt(row.qty) * flt(row.rate)
		frappe.db.set_value(
			"Sales Order Item",
			row.name,
			{"invoiced_amount": 0, "remaining_amount": total_amt},
		)
	frappe.db.commit()


@frappe.whitelist()
def get_so_items(sales_order):
	so = frappe.get_doc("Sales Order", sales_order)
	data = []
	for row in so.items:
		billed_qty, billed_amt = _get_billed_qty_and_amount(so.name, row.name)
		total_qty = flt(row.qty)
		total_rate = flt(row.rate)
		total_amt = total_qty * total_rate
		invoiced_amt = billed_amt
		remaining_amt = max(0, total_amt - billed_amt)
		remaining_qty = max(0, total_qty - billed_qty)
		remaining_qty_pct = (remaining_qty / total_qty * 100) if total_qty else 0
		remaining_amt_pct = (remaining_amt / total_amt * 100) if total_amt else 0
		is_stock = frappe.db.get_value("Item", row.item_code, "is_stock_item") or 0
		item_type = "Stock" if is_stock else "Service"
		has_remaining = remaining_qty > 0 or remaining_amt > 0
		data.append({
			"so_detail": row.name,
			"item_code": row.item_code,
			"qty": total_qty,
			"billed_qty": billed_qty,
			"remaining_qty": remaining_qty,
			"remaining_qty_percentage": round(remaining_qty_pct, 2),
			"rate": total_rate,
			"total_amt": total_amt,
			"billed_amt": invoiced_amt,
			"remaining_amt": remaining_amt,
			"invoiced_amount": invoiced_amt,
			"remaining_amt_percentage": round(remaining_amt_pct, 2),
			"item_type": item_type,
			"include": 0,
		})
	return data


@frappe.whitelist()
def make_sales_invoice_by_percentage(source_name, target_doc=None):
	""" Creates a sales invoice from a sales order based on the specified percentage for invoicing."""
	args = frappe.parse_json(frappe.form_dict.get("args") or "{}")
	percentage = flt(args.get("percentage"))
	apply_to_all = args.get("apply_to_all", True)
	selected_items = args.get("selected_items") or []
	if not selected_items:
		frappe.throw(_("Select at least one item"))
	so = frappe.get_doc("Sales Order", source_name)
	if so.docstatus != 1:
		frappe.throw(_("Sales Order must be submitted"))
	per_billed = flt(so.per_billed or 0)
	remaining_overall_pct = 100 - per_billed
	if apply_to_all:
		if not percentage or percentage <= 0:
			frappe.throw(_("Invalid Percentage"))
		if percentage > remaining_overall_pct:
			frappe.throw(_("Only {0}% remaining overall").format(remaining_overall_pct))
	selected_map = {d["so_detail"]: d for d in selected_items}
	si = make_sales_invoice(source_name, target_doc)
	new_items = []
	for item in si.items:
		if item.so_detail not in selected_map:
			continue
		sel = selected_map[item.so_detail]
		so_row = next((x for x in so.items if x.name == item.so_detail), None)
		if not so_row:
			continue
		item_type = sel.get("item_type") or "Stock"
		total_qty = flt(so_row.qty)
		total_rate = flt(so_row.rate)
		total_amt = total_qty * total_rate
		billed_qty = flt(sel.get("billed_qty") or 0)
		billed_amt = flt(sel.get("billed_amt") or 0)
		remaining_qty = flt(sel.get("remaining_qty") or max(0, total_qty - billed_qty))
		remaining_amt = flt(sel.get("remaining_amt") or max(0, total_amt - billed_amt))
		if apply_to_all:
			fraction = (percentage / remaining_overall_pct) if remaining_overall_pct else 0
		else:
			if not flt(sel.get("percentage")) or flt(sel.get("percentage")) <= 0:
				continue
		if item_type == "Stock":
			if remaining_qty <= 0:
				continue
			if apply_to_all:
				qty_to_bill = flt(remaining_qty * fraction, item.precision("qty"))
			else:
				item_pct = flt(sel.get("percentage")) / 100.0
				amt_to_bill = min(remaining_amt, flt(total_amt * item_pct, item.precision("amount")))
				qty_to_bill = (amt_to_bill / total_rate) if total_rate else 0
			qty_to_bill = min(flt(qty_to_bill, item.precision("qty")), remaining_qty)
			if qty_to_bill <= 0:
				continue
			item.qty = qty_to_bill
			item.rate = total_rate
		else:
			if remaining_amt <= 0:
				continue
			if apply_to_all:
				amt_to_bill = flt(remaining_amt * fraction, item.precision("amount"))
			else:
				item_pct = flt(sel.get("percentage")) / 100.0
				amt_to_bill = min(remaining_amt, flt(total_amt * item_pct, item.precision("amount")))
			amt_to_bill = min(amt_to_bill, remaining_amt)
			if amt_to_bill <= 0:
				continue
			item.qty = total_qty
			item.rate = (amt_to_bill / total_qty) if total_qty else 0
		new_items.append(item)
	if not new_items:
		frappe.throw(_("No items left to invoice"))
	si.set("items", new_items)
	si.calculate_taxes_and_totals()
	return si

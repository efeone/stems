import frappe
from frappe import _
from frappe.utils import flt

from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice


@frappe.whitelist()
def get_so_items(sales_order):
	"""
	Get Sales Order items with billed and remaining qty and percentage for percentage invoicing
	"""

	so = frappe.get_doc("Sales Order", sales_order)

	data = []

	for row in so.items:

		# Get billed qty properly
		billed_qty = frappe.db.sql("""
			SELECT SUM(sii.qty)
			FROM `tabSales Invoice Item` sii
			INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
			WHERE sii.sales_order = %s
			AND sii.so_detail = %s
			AND si.docstatus = 1
		""", (so.name, row.name))[0][0] or 0

		billed_qty = flt(billed_qty)
		total_qty = flt(row.qty)

		remaining_qty = total_qty - billed_qty

		if remaining_qty < 0:
			remaining_qty = 0

		if total_qty > 0:
			remaining_percentage = (remaining_qty / total_qty) * 100
		else:
			remaining_percentage = 0

		is_stock = frappe.db.get_value("Item", row.item_code, "is_stock_item") or 0

		data.append({
			"so_detail": row.name,
			"item_code": row.item_code,
			"qty": total_qty,
			"billed_qty": billed_qty,
			"remaining_qty": remaining_qty,
			"remaining_percentage": round(remaining_percentage, 2),
			"rate": flt(row.rate),
			"item_type": "Stock" if is_stock else "Service",
			"include": 1 if remaining_qty > 0 else 0
		})

	return data



@frappe.whitelist()
def make_sales_invoice_by_percentage(source_name, target_doc=None):
	"""
	Make Sales Invoice by % of Sales Order
	"""

	args = frappe.parse_json(frappe.form_dict.get("args") or "{}")

	percentage = flt(args.get("percentage"))
	selected_items = args.get("selected_items") or []

	if not percentage or percentage <= 0:
		frappe.throw(_("Invalid Percentage"))

	so = frappe.get_doc("Sales Order", source_name)

	if so.docstatus != 1:
		frappe.throw(_("Sales Order must be submitted"))

	# Header billed %
	per_billed = flt(so.per_billed or 0)
	remaining = 100 - per_billed

	if percentage > remaining:
		frappe.throw(_("Only {0}% remaining").format(remaining))

	selected_map = {d["so_detail"]: d for d in selected_items}

	si = make_sales_invoice(source_name, target_doc)

	new_items = []

	for item in si.items:

		if item.so_detail not in selected_map:
			continue

		so_row = next((x for x in so.items if x.name == item.so_detail), None)

		if not so_row:
			continue

		item_type = selected_map[item.so_detail]["item_type"]

		if item_type == "Stock":
			# Apply % on QTY
			new_qty = flt(so_row.qty * percentage / 100, item.precision("qty"))
			item.qty = new_qty
			item.rate = so_row.rate

		else:
			# Apply % on RATE
			new_rate = flt(so_row.rate * percentage / 100, item.precision("rate"))
			item.qty = so_row.qty
			item.rate = new_rate

		new_items.append(item)

	if not new_items:
		frappe.throw(_("No items selected"))

	si.set("items", new_items)

	si.calculate_taxes_and_totals()

	return si


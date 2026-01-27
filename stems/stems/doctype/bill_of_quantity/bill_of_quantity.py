# Copyright (c) 2025, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import today
from frappe import _
from frappe.utils.data import flt
from frappe.utils import get_url_to_form



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

@frappe.whitelist()
def transfer_stock_to_project(boq_name, items):
    """
    	Transfer stock from Item default warehouse to Project warehouse
    	based on BOQ items. Uses required_qty = qty - transferred_quantity.
    """
    boq_doc = frappe.get_doc("Bill of Quantity", boq_name)

    if not boq_doc.project:
        frappe.throw(_("Project is not linked to this BOQ"))

    items = frappe.parse_json(items)

    company = frappe.db.get_value("Project", boq_doc.project, "company")
    if not company:
        frappe.throw(_("Company not found in linked Project"))

    project_warehouse = frappe.db.get_single_value("STEMS Settings", "default_project_warehouse")
    if not project_warehouse:
        frappe.throw(_("Default Project Warehouse not set in STEMS Settings"))

    stock_entry = frappe.get_doc({
        "doctype": "Stock Entry",
        "stock_entry_type": "Material Transfer",
        "company": company,
        "items": []
    })

    transferred_any_item = False

    for transfer_row in items:
        item_code = transfer_row.get("item_code")
        transfer_qty = flt(transfer_row.get("qty"))

        if not item_code or transfer_qty <= 0:
            continue

        boq_item = next((row for row in boq_doc.items if row.item == item_code), None)
        if not boq_item:
            frappe.throw(_("Item {0} not found in BOQ").format(item_code))

        required_qty = flt(boq_item.qty) - flt(boq_item.transferred_quantity or 0)
        if required_qty <= 0:
            continue

        if transfer_qty > required_qty:
            frappe.throw(
                _("Cannot transfer more than required quantity for item {0}. Required: {1}")
                .format(item_code, required_qty)
            )

        from_warehouse = frappe.db.get_value(
            "Item Default",
            {"parent": item_code, "company": company},
            "default_warehouse"
        )
        if not from_warehouse:
            frappe.throw(
                _("Default Warehouse not set for Item {0} in Company {1}")
                .format(item_code, company)
            )

        stock_entry.append("items", {
            "item_code": item_code,
            "qty": transfer_qty,
            "s_warehouse": from_warehouse,
            "t_warehouse": project_warehouse
        })

        boq_item.transferred_quantity = flt(boq_item.transferred_quantity or 0) + transfer_qty
        transferred_any_item = True

    if not transferred_any_item:
        frappe.msgprint(_("All items are already transferred"))
        return

    stock_entry.insert()
    stock_entry.submit()
    boq_doc.save()

    frappe.msgprint(
    _('Stock successfully transferred to Project Warehouse.<br>'
      'Stock Entry: <a href="{0}">{1}</a>').format(get_url_to_form(stock_entry.doctype, stock_entry.name),stock_entry.name),alert=True,indicator='green')

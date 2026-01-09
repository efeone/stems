# Copyright (c) 2025, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc


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
        target.items = []
        target.required_items = []

        for row in source.items:
            row_data = {
                "item_code": row.item,
                "item_name": row.item_name,
                "qty": row.qty,
                "uom": row.uom,
                "customer_provided": row.customer_provided
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

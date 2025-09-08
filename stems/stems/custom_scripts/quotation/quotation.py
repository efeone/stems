import frappe
from frappe.model.mapper import get_mapped_doc
from frappe.utils import getdate, nowdate
from frappe import _
from erpnext.selling.doctype.quotation.quotation import _make_customer, get_ordered_items

@frappe.whitelist()
def make_sales_order_from_quotation(source_name: str, target_doc=None):
	if not frappe.db.get_singles_value(
		"Selling Settings", "allow_sales_order_creation_for_expired_quotation"
	):
		quotation = frappe.db.get_value(
			"Quotation", source_name, ["transaction_date", "valid_till"], as_dict=1
		)
		if quotation.valid_till and (
			quotation.valid_till < quotation.transaction_date or quotation.valid_till < getdate(nowdate())
		):
			frappe.throw(_("Validity period of this quotation has ended."))

	return make_customer_from_sales_order(source_name, target_doc)


def make_customer_from_sales_order(source_name, target_doc=None, ignore_permissions=False):
	customer = _make_customer(source_name, ignore_permissions)
	ordered_items = get_ordered_items(source_name)

	selected_rows = [x.get("name") for x in frappe.flags.get("args", {}).get("selected_items", [])]
	has_unit_price_items = frappe.db.get_value("Quotation", source_name, "has_unit_price_items")

	def is_unit_price_row(source) -> bool:
		return has_unit_price_items and source.qty == 0

	def set_missing_values(source, target):
		if customer:
			target.customer = customer.name
			target.customer_name = customer.customer_name

		if source.referral_sales_partner:
			target.sales_partner = source.referral_sales_partner
			target.commission_rate = frappe.get_value(
				"Sales Partner", source.referral_sales_partner, "commission_rate"
			)

		target.flags.ignore_permissions = ignore_permissions
		target.run_method("set_missing_values")
		target.run_method("calculate_taxes_and_totals")

	return get_mapped_doc(
		"Quotation",
		source_name,
		{
			"Quotation": {
				"doctype": "Sales Order",
				"validation": {"docstatus": ["=", 1]},
			},
			"Quotation Item": {
				"doctype": "Sales Order Item",
				"field_map": {
					"parent": "prevdoc_docname",
					"name": "quotation_item"
				},
				"condition": lambda d: d.qty > 0
			},
		},
		target_doc,
		set_missing_values,
	)

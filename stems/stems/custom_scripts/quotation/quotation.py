import frappe
from frappe.model.mapper import get_mapped_doc

@frappe.whitelist()
def make_sales_order_from_quotation(source_name, target_doc=None):
	"""
		Create a Sales Order from a Quotation.
	"""
	def set_missing_values(source, target):
		target.customer = source.party_name
		target.delivery_date = frappe.utils.nowdate()

	doclist = get_mapped_doc(
		"Quotation",
		source_name,
		{
			"Quotation": {
				"doctype": "Sales Order",
				"field_map": {
					"name": "quotation"        
				}
			},
			"Quotation Item": {
				"doctype": "Sales Order Item",
				"field_map": {
					"parent": "parent"
				}
			},
			"Required Items": {
				"doctype": "Sales Order Item",
				"field_map": {
					"parent": "parent"
				}
			}
		},
		target_doc,
		set_missing_values
	)
	return doclist

import frappe

def link_project_to_boq(doc, method=None):
	"""
	When a Project is created from a Sales Order,
	update the linked BOQ with the Project reference
	"""
	if not doc.sales_order:
		return
	
	sales_order = frappe.get_doc("Sales Order", doc.sales_order)
	if not sales_order.bill_of_quantity:
		return
	
	frappe.db.set_value("Bill of Quantity",sales_order.bill_of_quantity,"project",doc.name,update_modified=False)


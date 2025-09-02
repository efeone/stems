import frappe

@frappe.whitelist()
def create_enquiry(lead):
	"""Create a new Enquiry from Lead and return Enquiry name"""
	if not lead:
		frappe.throw("Lead is required to create Enquiry")

	lead_doc = frappe.get_doc("Lead", lead)

	# Create new Enquiry doc
	enquiry = frappe.new_doc("Enquiry")
	enquiry.from_lead = lead_doc.name
	enquiry.customer_name = lead_doc.lead_name  # adjust based on your field
	enquiry.email = lead_doc.email_id
	enquiry.phone = lead_doc.phone

	enquiry.insert(ignore_permissions=True)

	frappe.msgprint(f"Enquiry {enquiry.name} created successfully")

	return enquiry.name

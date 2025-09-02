import frappe

@frappe.whitelist()
def create_enquiry(lead):
    """Create a new Enquiry (Opportunity) from Lead and return Enquiry name"""
    if not lead:
        frappe.throw("Lead is required to create Enquiry")

    lead_doc = frappe.get_doc("Lead", lead)

    enquiry = frappe.new_doc("Opportunity")
    enquiry.opportunity_from = "Lead"
    enquiry.party_name = lead_doc.name
    enquiry.customer_name = lead_doc.lead_name
    enquiry.contact_email = lead_doc.email_id
    enquiry.contact_mobile = lead_doc.phone

    enquiry.insert(ignore_permissions=True)

    return enquiry.name
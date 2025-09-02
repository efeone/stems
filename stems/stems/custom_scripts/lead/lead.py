import frappe
from frappe.model.mapper import get_mapped_doc

@frappe.whitelist()
def make_enquiry(source_name, target_doc=None):
    """Create a new Enquiry (Opportunity) from Lead and return Enquiry name"""

    if not frappe.db.exists("Lead", source_name):
        frappe.throw(f"Lead {source_name} not found.")

    def set_missing_values(source, target):
        target.opportunity_from = "Lead"
        target.party_name = source.name
        target.customer_name = source.lead_name
        target.contact_email = source.email_id
        target.contact_mobile = source.phone

    doc = get_mapped_doc(
        "Lead",
        source_name,
        {
            "Lead": {
                "doctype": "Opportunity",
                "field_map": {
                    "name": "party_name",
                    "lead_name": "customer_name",
                    "email_id": "contact_email",
                    "phone": "contact_mobile"
                }
            }
        },
        target_doc,
        set_missing_values
    )
    return doc

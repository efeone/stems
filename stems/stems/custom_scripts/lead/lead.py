import frappe
from frappe.model.mapper import get_mapped_doc
from frappe.utils.user import get_users_with_role
from frappe.desk.form.assign_to import add as add_assignment, clear as clear_assignment
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

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_sales_user_employees(doctype, txt, searchfield, start, page_len, filters):
    """
    Fetch employees linked to users with the 'Sales User' role
    for filtering the Sales Person field in Lead.
    """
    users = get_users_with_role("Sales User")
    if not users:
        return []

    employees = frappe.get_all(
        "Employee",
        filters={
            "user_id": ["in", users],
            searchfield: ["like", f"%{txt}%"]
        },
        fields=["name", "employee_name"],
        start=start,
        page_length=page_len
    )

    return [(d.name, d.employee_name) for d in employees]

def auto_assign_lead(doc, method=None):
    """
    Assign Lead to the User linked to the Employee selected in Sales Person field.
    Runs on validate (before save). Uses an exist check to ensure assignment only after the Lead exists.
    """

    # Only assign if Sales Person is selected
    if not doc.sales_person:
        return

    # Check if the Lead exists in DB (not a new doc)
    if not frappe.db.exists("Lead", doc.name):
        return

    employee = doc.sales_person
    user_id = frappe.db.get_value("Employee", employee, "user_id")

    if not user_id:
        return

    # Clear old assignments to avoid duplicates
    clear_assignment("Lead", doc.name)

    # Create new assignment
    add_assignment({
        "assign_to": [user_id],
        "doctype": "Lead",
        "name": doc.name,
        "description": f"Auto-assigned Lead {doc.name} to {user_id}",
        "assigned_by": frappe.session.user
    })



import frappe
from frappe.model.mapper import get_mapped_doc
from frappe.email.doctype.email_template.email_template import get_email_template

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

def send_customer_approval_email(doc, method=None):
    """Send Quotation Approval email when workflow state = Pending Customer Approval"""

    if doc.workflow_state != "Pending Customer Approval":
        return

    settings = frappe.get_single("STEMS Settings")

    if not settings.enable_quotation_approval_notifcation:
        return

    if not settings.quotation_approval_notifcation_template:
        frappe.throw("Quotation Approval Notification Template is not set in STEMS Settings")

    template_data = {
        "quotation_number": doc.name,
        "quotation_date": doc.transaction_date,
        "total_amount": doc.total,
        "valid_till": doc.valid_till,
        "customer_name": doc.customer_name or doc.party_name,
        "company_name": doc.company,
        **doc.as_dict()
    }

    template = get_email_template(
        settings.quotation_approval_notifcation_template,
        template_data
    )

    customer_email = None
    if doc.quotation_to == "Lead":
        customer_email = frappe.db.get_value("Lead", doc.party_name, "email_id")
    elif doc.quotation_to == "Customer":
        customer_email = frappe.db.get_value("Customer", doc.party_name, "email_id")

    if not customer_email:
        frappe.throw(f"No email address found for {doc.quotation_to} {doc.party_name} in Quotation {doc.name}")

    attachments = None
    if settings.quotation_print_format:
        attachments = [
            frappe.attach_print(
                doc.doctype,
                doc.name,
                file_name=doc.name,
                print_format=settings.quotation_print_format
            )
        ]

    frappe.sendmail(
        recipients=[customer_email],
        subject=template.get("subject"),
        message=template.get("message"),
        reference_doctype=doc.doctype,
        reference_name=doc.name,
        attachments=attachments
    )
import frappe
from frappe.model.mapper import get_mapped_doc
from frappe.email.doctype.email_template.email_template import get_email_template
from frappe.utils import getdate, nowdate
from frappe import _
from erpnext.selling.doctype.quotation.quotation import _make_customer, get_ordered_items

@frappe.whitelist()
def make_sales_order_from_quotation(source_name: str, target_doc=None):
	"""
		Create a Sales Order from a Quotation.
		Delegate to `_make_sales_order_from_quotation` to perform actual mapping.
	"""
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

	return _make_sales_order_from_quotation(source_name, target_doc)

def _make_sales_order_from_quotation(source_name, target_doc=None, ignore_permissions=False):
	"""
		- Map only the standard `items` child table, ignoring `required_items`
		- Only map items with qty > 0.
		- Set customer details from Quotation.
		- If referral sales partner exists, map commission details.
		- Run standard ERPNext hooks: `set_missing_values` and `calculate_taxes_and_totals`.
	"""
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
				"condition": lambda d: d.parentfield == "items" and d.qty > 0
			},
		},
		target_doc,
		set_missing_values,
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

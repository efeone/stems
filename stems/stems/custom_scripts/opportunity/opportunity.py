import frappe
from frappe.model.document import Document
from frappe.desk.form.assign_to import add as add_assign
from frappe.utils.user import get_users_with_role

def on_update(doc, method=None):
	"""
	Triggered on Opportunity update.

	Args:
		doc (Document): The Opportunity document being updated.
		method (str, optional): The event hook method name (auto passed by Frappe).

	Description:
		- Runs whenever an Opportunity is updated.
		- If "Site Visit Required" is checked and a date is provided:
			→ Creates a Site Visit Event (calendar entry).
			→ Creates a Site Visit ToDo (task for the Site Engineer).
	"""
	if doc.site_visit_required and doc.site_visit_scheduled_on:
		create_site_visit_event(doc)
		create_site_visit_todo(doc)


def create_site_visit_event(doc):
	"""
	Create an Event for the site visit and add participants.
	This Event appears in "Open Events" under the Activities tab of the Opportunity.

	Args:
		doc (Document): The Opportunity document containing site visit details.

	Steps:
		1. Build a subject line using party name or lead name.
		2. Prevent duplicate Events for the same Opportunity.
		3. Create a new Event with subject, type, date, and reference to the Opportunity.
		4. Add participants:
			- Site Engineer (Employee)
			- Opportunity Owner
			- Linked Lead/Customer (if applicable)
		5. Save the Event.
	"""
	party = doc.party_name or doc.lead_name or "Unknown"

	existing_event = frappe.db.exists({
		"doctype": "Event",
		"reference_doctype": "Opportunity",
		"reference_name": doc.name,
		"subject": ["like", f"Site Visit - {party}%"]
	})
	if existing_event:
		return

	event = frappe.new_doc("Event")
	event.subject = f"Site Visit - {party}"
	event.event_type = "Private"
	event.starts_on = doc.site_visit_scheduled_on
	event.reference_doctype = "Opportunity"
	event.reference_docname = doc.name
	event.status = "Open"

	event.insert(ignore_permissions=True)

	# Add participants
	if doc.site_engineer:
		participant = event.append("event_participants", {})
		participant.reference_doctype = "Employee"
		participant.reference_docname = doc.site_engineer


	participant = event.append("event_participants", {})
	participant.reference_doctype = "Opportunity"
	participant.reference_docname = doc.name

	if doc.opportunity_from:
		participant = event.append("event_participants", {})
		participant.reference_doctype = doc.opportunity_from
		linked_docname = None
		if doc.opportunity_from == "Lead":
			linked_docname = doc.party_name or doc.lead_name
		elif doc.opportunity_from == "Customer":
			linked_docname = doc.customer_name
		if linked_docname:
			participant.reference_docname = linked_docname

	event.save(ignore_permissions=True)
	send_event_notification(event, doc)

def send_event_notification(event, opportunity):
	"""
	Send email notification to all participants of a Site Visit Event.
	"""
	template_name = frappe.db.get_single_value("STEMS Settings", "event_email_template")
	if not template_name:
		frappe.log_error(frappe.get_traceback(), "Event Email Template Missing in STEMS Settings")
		return

	recipients = set()
	for p in event.event_participants:
		if p.reference_doctype == "Employee":
			email = frappe.db.get_value(
				"Employee", p.reference_docname, "prefered_email"
			)
			if not email:
				user_id = frappe.db.get_value(
					"Employee", p.reference_docname, "user_id"
				)
				if user_id:
					email = frappe.db.get_value("User", user_id, "email")
			if email:
				recipients.add(email)
		elif p.reference_doctype == "Opportunity":
			email = frappe.db.get_value(
				"Opportunity",
				p.reference_docname,
				"contact_email"
			)
			if email:
				recipients.add(email)
		elif p.reference_doctype == "Customer":
			result = frappe.db.sql("""
				SELECT
					COALESCE(ce.email_id, c.email_id) AS email
				FROM `tabContact` c
				INNER JOIN `tabDynamic Link` dl
					ON dl.parent = c.name
				LEFT JOIN `tabContact Email` ce
					ON ce.parent = c.name
				   AND ce.is_primary = 1
				WHERE dl.link_doctype = 'Customer'
				  AND dl.link_name = %s
				  AND (ce.email_id IS NOT NULL OR c.email_id IS NOT NULL)
				LIMIT 1
			""", p.reference_docname, as_dict=True)

			if result and result[0].email:
				recipients.add(result[0].email)
		elif p.reference_doctype == "Lead":
			email = frappe.db.get_value("Lead", p.reference_docname, "email_id")
			if email:
				recipients.add(email)

	if not recipients:
		frappe.log_error(frappe.get_traceback(),f"No recipients for {event.name}")
		return

	template = frappe.get_doc("Email Template", template_name)
	context = {
		"event": event,
		"opportunity": opportunity,
		"party_name": opportunity.party_name,
		"starts_on": event.starts_on,
	}
	subject = frappe.render_template(template.subject, context)
	message = frappe.render_template(template.response, context)
	frappe.sendmail(
		recipients=list(recipients),
		subject=subject,
		message=message,
		reference_doctype="Event",
		reference_name=event.name,
	)

def create_site_visit_todo(doc):
	"""
	Create a ToDo for the site visit and assign it to the Site Engineer.
	This ToDo appears in "Open ToDos" under the Activities tab of the Opportunity.

	Args:
		doc (Document): The Opportunity document containing site visit details.

	Steps:
		1. Validate that Site Engineer is selected.
		2. Get the linked User from the Employee record.
		3. Prevent duplicate ToDos for the same Opportunity.
		4. Create a new ToDo assigned to the Site Engineer's User.
		5. Save the ToDo.
	"""
	if not doc.site_engineer:
		frappe.throw("Site Engineer not selected for this Opportunity.")

	user = frappe.db.get_value("Employee", doc.site_engineer, "user_id")
	if not user:
		frappe.throw(f"No User linked to Employee {doc.site_engineer}")

	existing_todo = frappe.db.exists({
		"doctype": "ToDo",
		"reference_type": "Opportunity",
		"reference_name": doc.name,
		"description": ["like", f"Site Visit - {doc.name}%"]
	})
	if existing_todo:
		return

	todo = frappe.new_doc("ToDo")
	todo.description = f"Site Visit - {doc.name}"
	todo.reference_type = "Opportunity"
	todo.reference_name = doc.name
	todo.allocated_to = user
	todo.status = "Open"
	todo.date = doc.site_visit_scheduled_on
	todo.insert(ignore_permissions=True)

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_site_engineers(doctype, txt, searchfield, start, page_len, filters):
    """
    Fetch employees linked to users with the 'Site Engineer' role
    for Link field searches.
    """
    users = get_users_with_role("Site Engineer")
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

@frappe.whitelist()
def make_boq(source_name, target_doc=None):
    """
    Create BOQ from Opportunity
    - customer_name from lead_name
    - party_name → lead in BOQ
    - fetch any Customer Need Profile for this enquiry (draft or submitted)
    - map items from Opportunity.items → BOQ.items
      only if item_code exists and qty > 0
      set BOQ item 'name' = Opportunity 'item_code'
    """

    def set_missing_values(source, target):
        target.opportunity = source.name

        if source.lead_name:
            target.customer_name = source.lead_name

        if getattr(source, "party_name", None):
            target.lead = source.party_name

        cnp = frappe.db.exists(
            "Customer Need Profile",
            {"enquiry": source.name}
        )
        if cnp:
            target.customer_need_profile = cnp

        if hasattr(source, "items") and source.items:
            for row in source.items:
                if row.item_code and row.qty > 0:
                    item = target.append("items", {})
                    item.item = row.item_code
                    item.item_name = row.item_name
                    item.qty = row.qty
                    item.uom = row.uom

    doc = frappe.model.mapper.get_mapped_doc(
        "Opportunity",
        source_name,
        {
            "Opportunity": {
                "doctype": "Bill of Quantity",
                "field_map": {
                    "name": "opportunity"
                }
            }
        },
        target_doc,
        set_missing_values
    )

    return doc

def update_lead_qualification_status(doc, method=None):
    """
    Update Lead qualification status when Opportunity is created from Lead
    """

    if doc.opportunity_from != "Lead":
        return

    lead_name = doc.party_name
    if not lead_name:
        return

    if not frappe.db.exists("Lead", lead_name):
        return

    current_status = frappe.db.get_value(
        "Lead",
        lead_name,
        "qualification_status"
    )

    if current_status != "Qualified":
        frappe.db.set_value(
            "Lead",
            lead_name,
            "qualification_status",
            "Qualified"
        )


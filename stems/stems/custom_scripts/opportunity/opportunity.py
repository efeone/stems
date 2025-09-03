import frappe
from frappe.model.document import Document
from frappe.desk.form.assign_to import add as add_assign


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
		"reference_type": "Opportunity",
		"reference_name": doc.name,
		"subject": ["like", f"Site Visit - {party}%"]
	})
	if existing_event:
		return

	event = frappe.new_doc("Event")
	event.subject = f"Site Visit - {party}"
	event.event_type = "Private"
	event.starts_on = doc.site_visit_scheduled_on
	event.reference_type = "Opportunity"
	event.reference_name = doc.name
	event.status = "Open"

	event.insert(ignore_permissions=True)

	# Add participants
	if doc.site_engineer:
		participant = event.append("event_participants", {})
		participant.reference_doctype = "Employee"
		participant.reference_docname = doc.site_engineer

	if doc.opportunity_owner:
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

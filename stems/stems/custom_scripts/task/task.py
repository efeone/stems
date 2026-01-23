# Copyright (c) 2025, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_url_to_form

def payment_requirement_notification(doc, method=None):
	"""
	Send payment requirement notification when a task is completed
	and payment is required.
	"""
	if doc.status != "Completed":
		return

	previous_doc = doc.get_doc_before_save()
	if previous_doc and previous_doc.status == "Completed":
		return

	if not doc.is_payment_required:
		return

	settings = frappe.get_single("STEMS Settings")
	if not settings.enable_payment_task_notification:
		frappe.log_error("Payment Task Notification Missing","Please enable payment task notifications in the settings.")
		return

	if not settings.payment_task_notification_role:
		frappe.log_error("Payment Task Notification Missing","Payment task notification role is not configured.")
		return

	if not settings.payment_task_notification_template:
		frappe.log_error("Payment Task Notification Missing","Payment task notification template is not configured.")
		return

	users = frappe.get_all(
		"Has Role",
		filters={"role": settings.payment_task_notification_role},
		fields=["parent"]
	)

	if not users:
		return

	template = frappe.get_doc(
		"Email Template",
		settings.payment_task_notification_template
	)

	for u in users:
		user = u.parent

		if not frappe.db.get_value("User", user, "enabled"):
			continue

		context = {
			"task_subject": doc.subject,
			"payment_percentage": doc.payment_percentage or 0,
			"project": doc.project,
		}

		subject = frappe.render_template(template.subject, context)
		message = frappe.render_template(template.response, context)

		frappe.get_doc({
			"doctype": "Notification Log",
			"subject": subject,
			"email_content": message,
			"for_user": user,
			"document_type": "Task",
			"document_name": doc.name
		}).insert(ignore_permissions=True)

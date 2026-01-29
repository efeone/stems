# Copyright (c) 2025, efeone and contributors
# For license information, please see license.txt

from annotated_types import doc
from pydoc import doc
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

def sync_task_payment_to_sales_order(doc, method):
	"""
	Sync task payment details to linked Sales Orders
	when a task is completed and payment is required
	"""

	if doc.status != "Completed":
		return

	if not doc.is_payment_required:
		return

	if not doc.project:
		return

	sales_orders = frappe.get_all(
		"Sales Order",
		filters={
			"project": doc.project,
			"docstatus": 1
		},
		pluck="name"
	)

	if not sales_orders:
		return

	for so_name in sales_orders:
		add_task_to_sales_order(so_name, doc)


def add_task_to_sales_order(so_name, task_doc):
	"""
	Add task-wise payment entry to Sales Order
	if it does not already exist
	"""

	so = frappe.get_doc("Sales Order", so_name)

	existing_tasks = [row.task for row in (so.task_wise_pay or [])]
	if task_doc.name in existing_tasks:
		return

	total = so.grand_total or 0
	percentage = task_doc.payment_percentage or 0

	so.append("task_wise_pay", {
		"task": task_doc.name,
		"percentage": percentage,
		"amount": (total * percentage) / 100,
		"add_to_print": 0
	})

	so.flags.ignore_permissions = True
	so.flags.ignore_validate_update_after_submit = True
	so.save()

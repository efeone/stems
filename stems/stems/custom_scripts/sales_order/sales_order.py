import frappe
from frappe.utils import get_datetime
from frappe.model.naming import make_autoname
from frappe.desk.form.assign_to import add as add_assignment

def generate_project_name(customer):
	series = make_autoname("PROJ-.####")
	serial = series.split("-")[-1]
	return f"{frappe.scrub(customer).upper()}-{serial}"

def get_task_templates_from_items(doc):
	"""Get list of existing task names from Item's task_template child table"""
	task_names = set()
	for item in doc.items:
		if not item.item_code:
			continue
		rows = frappe.get_all(
			"Task Templates",
			filters={"parent": item.item_code},
			pluck="task_templates"
		)
		for task_name in rows:
			if task_name:
				task_names.add(task_name)
	return list(task_names)

def assign_existing_tasks_to_project(project, doc):
	"""Link existing tasks from item templates to project and assign to employee group users"""
	task_names = get_task_templates_from_items(doc)
	if not task_names:
		return
	
	assignees = get_employee_group_users(doc.employee_group) if doc.employee_group else []
	for task_name in task_names:
		try:
			task = frappe.get_doc("Task", task_name)
			task.project = project.name
			task.save(ignore_permissions=True)
			
			for user in assignees:
				try:
					add_assignment({
						"assign_to": user,
						"doctype": "Task",
						"name": task_name,
						"description": f"Task assigned from Sales Order {doc.name}"
					})
				except Exception as e:
					frappe.log_error(f"Failed to assign task {task_name} to {user}: {str(e)}")
		except Exception as e:
			frappe.log_error(f"Failed to link task {task_name} to project: {str(e)}")

def create_project_from_sales_order(doc, method=None):
	"""Create a Project from Sales Order on submission"""
	if doc.project:
		return
	
	project_name = doc.project_name or generate_project_name(doc.customer)
	expected_end_date = doc.delivery_date
	project = frappe.get_doc({
		"doctype": "Project",
		"project_name": project_name,
		"customer": doc.customer,
		"sales_order": doc.name,
		"expected_start_date": doc.transaction_date,
		"expected_end_date": expected_end_date,
	}).insert(ignore_permissions=True)
	
	assign_existing_tasks_to_project(project, doc)
	assign_project_to_employee_group(project, doc)
	send_project_notification(project, doc)

def assign_project_to_employee_group(project, doc):
	"""Assign the project itself to all users in the employee group"""
	if not doc.employee_group:
		return
	
	employee_group = frappe.get_doc("Employee Group", doc.employee_group)
	for row in employee_group.employee_list:
		if not row.user_id:
			continue
		try:
			add_assignment({
				"assign_to": [row.user_id],
				"doctype": "Project",
				"name": project.name,
				"description": f"Project assigned from Sales Order {doc.name}"
			})
		except Exception as e:
			frappe.log_error(f"Failed to assign project to {row.user_id}: {str(e)}")

def send_project_notification(project, doc):
	"""Send email notification to employee group users"""
	template_name = frappe.get_single_value("STEMS Settings", "project_assignment_notification")
	if not template_name:
		return
	
	try:
		template = frappe.get_doc("Email Template", template_name)        
		context = {
			"project": project,
			"sales_order": doc,
		}
		
		subject = frappe.render_template(template.subject, context)
		message = frappe.render_template(template.response, context)
		
		recipients = get_employee_group_users(doc.employee_group)
		if not recipients:
			return
		
		frappe.sendmail(
			recipients=recipients,
			subject=subject,
			message=message
		)
	except Exception as e:
		frappe.log_error(
			title="Failed to send project notification",
			message=frappe.get_traceback()
		)

def get_employee_group_users(employee_group):
	"""Get list of user IDs from employee group"""
	if not employee_group:
		return []
	
	group = frappe.get_doc("Employee Group", employee_group)
	return [row.user_id for row in group.employee_list if row.user_id]

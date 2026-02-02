import frappe
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
		frappe.log_error(message=f"No task templates found for Sales Order {doc.name}",title="Task Template Missing")
		return
	
	for task_name in task_names:
		try:
			task = frappe.get_doc("Task", task_name)
			new_task = frappe.get_doc({
				"doctype": "Task",
				"subject": task.subject,
				"description": task.description,
				"expected_time": task.expected_time,
				"project": project.name,
				"status": "Open",
			}).insert(ignore_permissions=True)
		except Exception as e:
			frappe.log_error(f"Failed to link task {new_task.name} to project: {str(e)}")

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

def assign_project_to_employee_group(project, doc):
	"""Assign the project itself to all users in the employee group"""
	if not doc.employee_group:
		frappe.log_error(message=f"No employee group specified for Sales Order {doc.name}",title="Employee Group Missing")
		return
	
	users = get_employee_group_users(doc.employee_group)
	if not users:
		return
	try:
		add_assignment({
			"assign_to": users,
			"doctype": "Project",
			"name": project.name,
			"description": f"Project assigned from Sales Order {doc.name}"
		})
	except Exception as e:
		frappe.log_error(f"Failed to assign project to users: {str(e)}")

def get_employee_group_users(employee_group):
	"""Get list of user IDs from employee group"""
	if not employee_group:
		frappe.log_error(message="Employee group not specified", title="Employee Group Error")
		return []
	
	group = frappe.get_doc("Employee Group", employee_group)
	return [row.user_id for row in group.employee_list if row.user_id]

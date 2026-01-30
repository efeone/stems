def get_sales_order_custom_fields():
	"""
	Custom fields that need to be added to the Sales Order DocType
	"""
	return {
		"Sales Order": [
			{
				"fieldname": "bill_of_quantity",
				"fieldtype": "Link",
				"options": "Bill of Quantity",
				"label": "Bill of Quantity",
				"insert_after": "order_type",
			},
			{
				"fieldname": "section_break_project",
				"fieldtype": "Section Break",
				"label": "",
				"insert_after": "reserve_stock",
			},
			{
				"fieldname": "employee_group",
				"fieldtype": "Link",
				"options": "Employee Group",
				"label": "Employee Group",
				"insert_after": "section_break_project",
			},
			{
				"fieldname": "column_break_project",
				"fieldtype": "Column Break",
				"label": "",
				"insert_after": "employee_group",
			},
			{
				"fieldname": "project_name",
				"fieldtype": "Data",
				"label": "Project Name",
				"insert_after": "column_break_project",
			},
		]
	}


def get_item_custom_fields():
	'''
		Method to get custom fields to be created for Lead
	'''
	return {
		"Item": [
			{
				"fieldname": "is_cnp_item",
				"fieldtype": "Check",
				"insert_after": "has_variants",
				"label": "Is CNP Item",
			},
			{
				"fieldname": "section_break_template",
				"fieldtype": "Section Break",
				"insert_after": "is_fixed_asset",
				"label": "",
			},
			{
				"fieldname": "task_template",
				"fieldtype": "Table",
				"options": "Task Templates",
				"insert_after": "section_break_template",
				"label": "Task Templates",
			},
		]
	}

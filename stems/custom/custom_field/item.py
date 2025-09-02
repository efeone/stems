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
		]
	}

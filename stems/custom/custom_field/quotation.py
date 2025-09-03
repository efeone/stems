def get_quotation_custom_fields():
	"""
	Custom fields that need to be added to the Quotation DocType
	"""
	return {
		"Quotation": [
			{
				"fieldname": "customer_need_profile",
				"fieldtype": "Link",
				"options": "Customer Need Profile",
				"label": "Customer Need Profile",
				"insert_after": "customer_name",
			},
			{
				"fieldname": "required_items",
				"fieldtype": "Table",
				"options": "Quotation Item",
				"label": "Required Items",
				"insert_after": "items",
			},
		]
	}

def get_stock_entry_custom_fields():
	"""
	Custom fields that need to be added to the Stock Entry DocType
	"""
	return {
		"Stock Entry": [
			{
				"fieldname": "boq_reference",
				"fieldtype": "Link",
				"options": "Bill of Quantity",
				"label": "BOQ Reference",
				"insert_after": "stock_entry_type",
			},
		]
	}

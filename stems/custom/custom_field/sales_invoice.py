def get_sales_invoice_custom_fields():
	"""
	Custom fields for Sales Invoice (and child) for percentage invoicing from Sales Order.
	"""
	return {
		"Sales Invoice Item": [
			{
				"fieldname": "billed_percentage",
				"fieldtype": "Percent",
				"label": "Billed %",
				"insert_after": "amount",
				"read_only": 1,
			},
			{
				"fieldname": "remaining_percentage",
				"fieldtype": "Percent",
				"label": "Remaining %",
				"insert_after": "billed_percentage",
				"read_only": 1,
			},
		]
	}

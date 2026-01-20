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
				"insert_after": "customer_need_profile",
			},
		]
	}


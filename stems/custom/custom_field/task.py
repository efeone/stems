def get_task_custom_fields():
	'''
		Method to get custom fields to be created for Task
	'''
	return {
		"Task": [
			{
				"fieldname": "is_payment_required",
				"fieldtype": "Check",
				"insert_after": "parent_task",
				"label": "Payment Required",
			},
			{
				"fieldname": "payment_percentage",
				"fieldtype": "Percent",
				"insert_after": "is_payment_required",
				"label": "Payment Percentage",
				"depends_on": "eval:doc.is_payment_required == 1",
				"mandatory_depends_on": "eval:doc.is_payment_required == 1",
			},
		]
	}

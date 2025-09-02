def get_opportunity_custom_fields():
	'''
	Custom fields that need to be added to the Opportunity DocType
	'''
	return {
		"Opportunity": [
			{
				"fieldname": "site_visit_required",
				"label": "Site Visit Required",
				"fieldtype": "Check",
				"insert_after": "opportunity_from",
			},
			{
				"fieldname": "drawing_required",
				"label": "Drawing Required",
				"fieldtype": "Check",
				"insert_after": "site_visit_required",
			},
			{
				"fieldname": "site_visit_scheduled_on",
				"label": "Site Visit Scheduled On",
				"fieldtype": "Date",
				"insert_after": "drawing_required",
				"depends_on": "eval:doc.site_visit_required",
				"mandatory_depends_on": "eval:doc.site_visit_required",
			},
			{
				"fieldname": "site_engineer",
				"label": "Site Engineer / Supervisor",
				"fieldtype": "Link",
				"options": "Employee",
				"insert_after": "site_visit_scheduled_on",
				"depends_on": "eval:doc.site_visit_required",
				"mandatory_depends_on": "eval:doc.site_visit_required",
				"ignore_user_permissions": 1
			},
						{
				"fieldname": "lead_name",
				"label": "Lead Name",
				"fieldtype": "Data",
				"insert_after": "party_name",
				"fetch_from": "lead.lead_name",
				"read_only": 1
			},
		]
	}

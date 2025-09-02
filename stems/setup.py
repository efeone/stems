import os
import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.desk.page.setup_wizard.setup_wizard import make_records

def after_install():
	create_custom_fields(get_lead_custom_fields(), ignore_validate=True)
	create_custom_fields(get_opportunity_custom_fields(), ignore_validate=True)
	create_translations(get_custom_translations())

	create_custom_roles(get_stems_roles())

def after_migrate():
	after_install()

def before_uninstall():
	delete_custom_fields(get_lead_custom_fields())
	delete_custom_fields(get_opportunity_custom_fields())

def create_custom_roles(roles):
	'''
		Method to create custom Role
		args:
			roles : Role List (list of string)
		example:
			["HOD", "Manager"]
	'''
	for role in roles:
		if not frappe.db.exists("Role", role):
			role_doc = frappe.get_doc({
				"doctype": "Role",
				"role_name": role
			})
			role_doc.insert(ignore_permissions=True)
	frappe.db.commit()

def create_translations(translations):
	for translation in translations:
		if not frappe.db.exists(translation):
			frappe.get_doc(translation).insert(ignore_permissions=True)
	frappe.db.commit()

def get_custom_translations():
	'''
		Method to get Translations
	'''
	return [
		{
			'doctype': 'Translation',
			'source_text': 'Opportunity',
			'translated_text': 'Enquiry',
			'language': 'en'
		}
	]

def get_stems_roles():
	'''
		Method to get Stems specific roles
	'''
	return ['Site Engineer','Drawing User']



def delete_custom_fields(custom_fields: dict):
	'''
	Method to Delete custom fields
	args:
		custom_fields: a dict like `{'Task': [{fieldname: 'your_fieldname', ...}]}`
	'''
	for doctype, fields in custom_fields.items():
		frappe.db.delete(
			"Custom Field",
			{
				"fieldname": ("in", [field["fieldname"] for field in fields]),
				"dt": doctype,
			},
		)
		frappe.clear_cache(doctype=doctype)


def get_lead_custom_fields():
	'''
	Custom fields that need to be added to the Lead DocType
	'''
	return {
		"Lead": [
		
		
		]
	}

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


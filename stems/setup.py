import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

# Custom field method imports
from stems.custom.custom_field.item import get_item_custom_fields

def after_migrate():
	# Creating STEMS specific custom fields
	create_custom_fields(get_custom_fields(), ignore_validate=True)

	# Creating STEMS specific Property Setters
	create_property_setters(get_property_setters())

def before_migrate():
	delete_custom_fields_for_stems()

def create_custom_fields_for_stems():
	create_custom_fields(get_custom_fields())

def create_property_setters_for_stems():
    create_property_setters(get_property_setters())

def delete_custom_fields_for_stems():
	delete_custom_fields(get_custom_fields())
 
def delete_custom_fields(custom_fields: dict):
	'''
		Method to Delete custom fields
		args:
			custom_fields: a dict like `{"Item": [{fieldname: "is_pixel", ...}]}`
	'''
	for doctype, fields in custom_fields.items():
		frappe.db.delete(
			'Custom Field',
			{
				'fieldname': ('in', [field.get('fieldname') for field in fields]),
				'dt': doctype,
			},
		)
		frappe.clear_cache(doctype=doctype)

def create_property_setters(property_setter_datas):
	'''
		Method to create custom property setters
		args:
			property_setter_datas : list of dict of property setter obj
	'''
	for property_setter_data in property_setter_datas:
		if frappe.db.exists('Property Setter', property_setter_data):
			continue
		property_setter = frappe.new_doc('Property Setter')
		property_setter.update(property_setter_data)
		property_setter.flags.ignore_permissions = True
		property_setter.insert()

def get_custom_fields():
	'''
		Method to get custom fields to be created for STEMS
	'''
	custom_fields = get_item_custom_fields()
	return custom_fields

def get_property_setters():
	'''
		STEMS specific property setters that need to be added to the Standard DocTypes
	'''
	property_setters = []
	return property_setters

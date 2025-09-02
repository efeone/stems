# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from stems.setup import (
    create_custom_fields_for_stems,
    create_property_setters_for_stems,
    delete_custom_fields_for_stems,
)

def insert_doc(doc_list):
    for doc in doc_list:
        frappe.get_doc(doc).insert(ignore_permissions=True)

def after_install():
    create_custom_fields_for_stems()
    create_property_setters_for_stems()


def before_uninstall():
    delete_custom_fields_for_stems()
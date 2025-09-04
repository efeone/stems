// Copyright (c) 2025, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Bill of Quantity', {
    refresh: function(frm) {
        if (!frm.is_new()) {
            add_make_quotation_button(frm);
        }
    }
});

/*
 * Add button to create Quotation from Bill of Quantity
 */
function add_make_quotation_button(frm) {
    frm.add_custom_button(__('Quotation'), function() {
        frappe.model.open_mapped_doc({
            method: "stems.stems.doctype.bill_of_quantity.bill_of_quantity.make_quotation",
            frm: frm
        });
    }, __("Create"));
}

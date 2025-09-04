// Copyright (c) 2025, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('STEMS Settings', {
	refresh: function(frm) {
		set_quotation_print_format(frm);
	}
});

/*
 * filter Quotation Print Format to show only those with doc_type as Quotation
 */
function set_quotation_print_format(frm) {
	frm.set_query('quotation_print_format', () => {	
		return {
			filters: {
				doc_type: 'Quotation'
			}
		}
	});	
}
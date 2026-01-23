// Copyright (c) 2025, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('STEMS Settings', {
	refresh: function(frm) {
		set_quotation_print_format(frm);
	},
	enable_payment_task_notification: function (frm) {
		handle_payment_task_notification_toggle(frm);
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

/*
 * Function to handle clearing fields when Payment Task Notification is disabled
 */
function handle_payment_task_notification_toggle(frm) {
	if (!frm.doc.enable_payment_task_notification) {
		frm.set_value('payment_task_notification_template', '');
		frm.set_value('payment_task_notification_role', '');

		frm.refresh_field('payment_task_notification_template');
		frm.refresh_field('payment_task_notification_role');
	}
}


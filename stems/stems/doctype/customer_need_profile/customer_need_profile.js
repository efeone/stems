// Copyright (c) 2025, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on("Customer Need Profile", {
	refresh: function(frm) {
		set_site_engineer_query(frm);
		set_customer_needs_item_query(frm);

		if (!frm.is_new() && frm.doc.docstatus === 1) {
			add_bill_of_quantity_button(frm);
		}
	}
});

/*
 * Set query for site_engineer_supervisor
 */
function set_site_engineer_query(frm) {
	frm.set_query("site_engineer_supervisor", function() {
		return {
			query: "stems.stems.doctype.customer_need_profile.customer_need_profile.get_site_engineers"
		};
	});
}

/*
 * Set query for item in child table customer_needs
 */
function set_customer_needs_item_query(frm) {
	frm.set_query('item', 'customer_needs', () => {
		return {
			filters: {
				is_cnp_item: 1,
				is_sales_item: 1
			}
		}
	});
}

/*
 * Add button to create Bill of Quantity
 */
function add_bill_of_quantity_button(frm){
	frm.add_custom_button(__('Bill of Quantity'), function() {
		frappe.model.open_mapped_doc({
			method: "stems.stems.doctype.customer_need_profile.customer_need_profile.make_bill_of_quantity",
			frm: frm
		});
	}, __("Create"));
}

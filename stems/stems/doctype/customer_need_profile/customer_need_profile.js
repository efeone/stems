// Copyright (c) 2025, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on("Customer Need Profile", {
	refresh: function(frm) {
		set_site_engineer_query(frm);
		set_customer_needs_item_query(frm);
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

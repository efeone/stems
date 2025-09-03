frappe.ui.form.on("Opportunity", {
	refresh: function(frm) {
		if (!frm.is_new()) {
			add_customer_need_profile_button(frm);
		}
		set_item_code_query(frm);
        set_site_engineer_query(frm);
	}
});

/*
 * Add custom button for creating Customer Need Profile
 */
function add_customer_need_profile_button(frm) {
	frm.add_custom_button(__('Customer Need Profile'), function() {
		frappe.model.open_mapped_doc({
			method: "stems.stems.doctype.customer_need_profile.customer_need_profile.make_customer_need_profile",
			frm: frm
		});
	}, __("Create"));
}

/*
 * Set query for item_code in child table
 */
function set_item_code_query(frm) {
	frm.set_query('item_code', 'items', () => {
		return {
			filters: {
				is_cnp_item: 1,
				is_sales_item: 1
			}
		}
	});
}

/*
 * Set query for site_engineer
 */
function set_site_engineer_query(frm) {
    frm.set_query("site_engineer", function() {
        return {
            query: "stems.stems.custom_scripts.opportunity.opportunity.get_site_engineers"
        };
    });
}
frappe.ui.form.on("Lead", {
	refresh: function(frm) {
		setTimeout(() => {
			frm.remove_custom_button("Opportunity", "Create");
			frm.remove_custom_button("Prospect", "Create");

			if (frm.page && frm.page.remove_inner_button) {
				frm.page.remove_inner_button("Opportunity", "Create");
			}

		if (!frm.is_new()) {
			frm.add_custom_button(__('Enquiry'), function() {
				frappe.model.open_mapped_doc({
					method: "stems.stems.custom_scripts.lead.lead.make_enquiry",
					source_name: frm.doc.name
				});
			}, __("Create"));
		}
		}, 10); 
	},
	setup: function(frm) {
		set_sales_person_query(frm);
    }
});

/*
 * Set query for Sales User
 */
function set_sales_person_query(frm) {
    frm.set_query("sales_person", function() {
        return {
            query: "stems.stems.custom_scripts.lead.lead.get_sales_user_employees"
        };
    });
}

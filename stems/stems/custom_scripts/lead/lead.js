frappe.ui.form.on("Lead", {
    refresh: function(frm) {
        setTimeout(() => {
            // Remove Create buttons
            frm.remove_custom_button("Opportunity", "Create");
            frm.remove_custom_button("Prospect", "Create");
            if (frm.page && frm.page.remove_inner_button) {
                frm.page.remove_inner_button("Opportunity", "Create");
                frm.page.remove_inner_button("Prospect", "Create");
            }

            // Remove Action button
            frm.remove_custom_button("Add to Prospect", "Action");
            if (frm.page && frm.page.remove_inner_button) {
                frm.page.remove_inner_button("Add to Prospect", "Action");
            }

            // Add Enquiry button under Create group
            if (!frm.is_new()) {
                frm.add_custom_button(__('Enquiry'), function() {
                    frappe.model.open_mapped_doc({
                        method: "stems.stems.custom_scripts.lead.lead.make_enquiry",
                        source_name: frm.doc.name
                    });
                }, __("Create"));
            }
        }, 100);
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

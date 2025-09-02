frappe.ui.form.on("Lead", {
    refresh: function(frm) {
        frm.remove_custom_button("Opportunity", "Create");
        frm.page.remove_inner_button('Opportunity', 'Create');

        frm.add_custom_button(__("Enquiry"), function() {
            frappe.call({
                method: "stems.stems.custom_scripts.lead.lead.create_enquiry",
                args: {
                    lead: frm.doc.name
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.set_route("Form", "Opportunity", r.message);
                    }
                }
            });
        }, __("Create"));
    }
});

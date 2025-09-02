frappe.ui.form.on("Opportunity", {
    refresh: function(frm) {
        frm.fields_dict['site_engineer'].get_query = function(doc) {
            return {
                query: "frappe.core.doctype.user.user.get_employees_based_on_role",
                filters: {
                    role: "Site Engineer"
                }
            };
        };
    }
});

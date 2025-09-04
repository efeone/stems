frappe.listview_settings['Lead'] = {
    onload: function(listview) {
        listview.page.add_inner_button(__('Assign Sales Person'), function() {

            // Get selected leads from the list view
            const selected_leads = listview.get_checked_items();

            if (!selected_leads.length) {
                frappe.msgprint(__('Please select at least one Lead'));
                return;
            }

            const d = new frappe.ui.Dialog({
                title: __('Assign Sales Person'),
                fields: [
                    {
                        label: 'Sales Person',
                        fieldname: 'sales_user',
                        fieldtype: 'Link',
                        options: 'Employee',
                        get_query: function() {
                            return {
                                query: 'stems.stems.custom_scripts.lead.lead.get_sales_user_employees'
                            };
                        },
                        reqd: 1
                    }
                ],
                primary_action_label: 'Assign',
                primary_action: function(values) {
                    const sales_user = values.sales_user;

                    if (!sales_user) {
                        frappe.msgprint(__('Please select a Sales Person'));
                        return;
                    }

                    // Call backend method to assign each lead to selected sales person
                    frappe.call({
                        method: "stems.stems.custom_scripts.lead.lead.bulk_assign_lead",
                        args: {
                            docnames: selected_leads.map(l => l.name),
                            sales_user: sales_user
                        },
                        callback: function(r) {
                            if (!r.exc) {
                                frappe.show_alert({
                                    message: __('Assigned {0} lead(s) to {1}', [selected_leads.length, sales_user]),
                                    indicator: 'green'
                                });
                                listview.refresh();
                            }
                        }
                    });

                    d.hide();
                }
            });

            d.show();
        });
    }
};

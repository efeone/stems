// // File: stems/custom_scripts/lead/lead.js

// frappe.listview_settings['Lead'] = {
//     onload(listview) {
//         listview.page.add_inner_button(__('Assign Salespersons'), function() {
//             // Prompt user to select Employee to assign
//             frappe.prompt({
//                 fieldname: 'sales_person',
//                 fieldtype: 'Link',
//                 label: 'Sales Person',
//                 options: 'Employee',
//                 reqd: 1
//             }, async function(values) {
//                 const emp = values.sales_person;

//                 // Get linked user for Employee
//                 let emp_user = await frappe.db.get_value('Employee', emp, 'user_id');
//                 if (!emp_user || !emp_user.message.user_id) {
//                     frappe.msgprint(__('Selected Employee has no linked User'));
//                     return;
//                 }

//                 const user_id = emp_user.message.user_id;

//                 // Check if linked user has Sales User role
//                 const role_check = await frappe.call({
//                     method: "frappe.client.get_list",
//                     args: {
//                         doctype: "Has Role",
//                         filters: { parent: user_id, role: "Sales User" },
//                         fields: ["role"]
//                     }
//                 });

//                 if (!role_check.message.length) {
//                     frappe.msgprint(__('Selected Employee is not a Sales User'));
//                     return;
//                 }

//                 // Get selected Leads in ListView
//                 const selected_leads = listview.get_checked_items();
//                 if (!selected_leads.length) {
//                     frappe.msgprint(__('Please select at least one Lead'));
//                     return;
//                 }

//                 // Assign the selected Employee to each Lead
//                 for (let lead of selected_leads) {
//                     await frappe.db.set_value('Lead', lead.name, 'sales_person', emp);
//                 }

//                 frappe.msgprint(__('Assigned {0} to {1} Leads', [emp, selected_leads.length]));
//                 listview.refresh();
//             }, __('Assign Sales Person'), __('Assign'));
//         });
//     }
// };


frappe.listview_settings['Lead'] = {
    onload: function(listview) {
        listview.page.add_inner_button(__('Assign to Sales Users'), async function() {
            let selected = listview.get_checked_items();
            if (!selected.length) {
                frappe.msgprint(__('Please select at least one record'));
                return;
            }

            for (let doc of selected) {
                let result = await frappe.call({
                    method: "stems.stems.custom_scripts.lead.lead.assign_to_sales_users",
                    args: { docname: doc.name }
                });
                frappe.msgprint(__('Assigned to: ') + result.message.join(", "));
            }
            listview.refresh();
        });
    }
};

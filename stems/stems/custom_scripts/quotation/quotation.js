frappe.ui.form.on('Quotation', {
	refresh: function(frm) {
		setTimeout(() => {
			remove_default_sales_order_button(frm);
			add_custom_sales_order_button(frm);
		}, 5);
	}
});

/**
 * Remove the default Sales Order button under "Create"
 */
function remove_default_sales_order_button(frm) {
	frm.remove_custom_button('Sales Order', 'Create');
}

/**
 * Add a custom Sales Order button under "Create"
 * Only visible if Quotation is Customer Approved
 */
function add_custom_sales_order_button(frm) {
	if (frm.doc.docstatus === 1 && frm.doc.workflow_state === "Customer Approved") {
		frm.add_custom_button(__('Sales Order'), () => {
			frappe.model.open_mapped_doc({
				method: 'stems.stems.custom_scripts.quotation.quotation.make_sales_order_from_quotation',
				frm: frm
			});
		}, __('Create'));
	}
}
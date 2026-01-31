frappe.ui.form.on('Delivery Note', {
	refresh(frm) {
		set_source_warehouse(frm);
	},
	project (frm) {
		set_source_warehouse(frm);
	}
});

/**
 * Sets the Delivery Note's warehouse from STEMS Settings if a project is selected,
 * or clears it if no project is linked.
 */
function set_source_warehouse(frm) {
	if (frm.doc.project) {
		frappe.db.get_single_value('STEMS Settings', 'default_project_warehouse')
			.then(warehouse => {
				if (warehouse) {
					frm.set_value('set_warehouse', warehouse);
				}
			});
	} else {
		frm.set_value('set_warehouse', '');
	}
}

frappe.ui.form.on('Delivery Note', {
	project (frm) {
		if (frm.doc.project) {
			frappe.call({
				method: 'stems.stems.custom_scripts.delivery_note.delivery_note.get_default_project_warehouse',
				callback: function (r) {
					if (r.message) {
						frm.set_value('set_warehouse', r.message);
					}
				}
			});
		} else {
			frm.set_value('set_warehouse', '');
		}
	}
});
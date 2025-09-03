frappe.ui.form.on("Lead", {
	refresh: function(frm) {
		frm.remove_custom_button("Opportunity", "Create");
		frm.page.remove_inner_button("Opportunity", "Create");

		if (!frm.is_new()) {
			frm.add_custom_button(__('Enquiry'), function() {
				frappe.model.open_mapped_doc({
					method: "stems.stems.custom_scripts.lead.lead.make_enquiry",
					source_name: frm.doc.name
				});
			}, __("Create"));
		}
	}
});

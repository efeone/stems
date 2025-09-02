frappe.ui.form.on("Lead", {
	refresh: function(frm) {
		// Remove default Opportunity button
		frm.remove_custom_button("Opportunity", "Create");

		frm.page.remove_inner_button('Opportunity', 'Create');


		// Add Enquiry button
		frm.add_custom_button(__("Enquiry"), function() {
			frappe.call({
				method: "stems.stems.doctype.lead.lead.create_enquiry",
				args: {
					lead: frm.doc.name
				},
				callback: function(r) {
					if (r.message) {
						frappe.set_route("Form", "Enquiry", r.message);
					}
				}
			});
		}, __("Create")); // group it under Create menu
	}
});

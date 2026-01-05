frappe.ui.form.on("Lead", {
	refresh: function(frm) {
		setTimeout(() => {
			customize_lead_buttons(frm);
		}, 100);
	},
	setup: function(frm) {
		set_sales_person_query(frm);
	},
	sales_person: function(frm) {
		set_lead_owner_from_sales_person(frm);
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

/*
 * Function to Add and remove custom buttons on Lead form
 */
function customize_lead_buttons(frm) {
	frm.remove_custom_button("Opportunity", "Create");
	frm.remove_custom_button("Prospect", "Create");
	if (frm.page && frm.page.remove_inner_button) {
		frm.page.remove_inner_button("Opportunity", "Create");
		frm.page.remove_inner_button("Prospect", "Create");
	}

	// Remove Action buttons
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
}

/**
 * Helper function to sync Lead Owner with Sales Person
 */
function set_lead_owner_from_sales_person(frm) {

	if (!frm.doc.sales_person) {
		frm.set_value("lead_owner", frm.doc.owner);
		return;
	}

	frappe.db.get_value(
		"Employee",
		frm.doc.sales_person,
		"user_id",
		function(r) {
			if (r && r.user_id) {
				frm.set_value("lead_owner", r.user_id);
			}
			else{
				frm.set_value("lead_owner", null);
			}
		}
	);
}

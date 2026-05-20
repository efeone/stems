// Copyright (c) 2026, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on("VAT Settings", {
	refresh: function (frm) {
		frm.set_query("account", "vat_accounts", function () {
			return {
				filters: {
					company: frm.doc.company,
					account_type: "Tax",
					is_group: 0,
				},
			};
		});
	},
});
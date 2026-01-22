// Copyright (c) 2025, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Bill of Quantity', {
	refresh: function(frm) {
		if (!frm.is_new()) {
			add_make_quotation_button(frm);
			add_create_rfq_button(frm);
		}
	},
	after_save: function(frm) {
		show_additional_stock_message(frm);
	},
	onload : function(frm) {
		frm.doc.items.forEach(function(row, index) {
				stock_balance_fetch(frm, 'Bill of Quantity Item', row.name);
		});
	}
});

/*
* Add button to create Quotation from Bill of Quantity
*/
function add_make_quotation_button(frm) {
	frm.add_custom_button(__('Quotation'), function() {
		frappe.model.open_mapped_doc({
			method: "stems.stems.doctype.bill_of_quantity.bill_of_quantity.make_quotation",
			frm: frm
		});
	}, __("Create"));
}

frappe.ui.form.on('Bill of Quantity Item', {
	item: function(frm, cdt, cdn) {
		stock_balance_fetch(frm, cdt, cdn);
	},
	qty: function(frm, cdt, cdn) {   
		calculate_additional_qty(frm, cdt, cdn);
	},
	stock_balance: function(frm, cdt, cdn) {
		calculate_additional_qty(frm, cdt, cdn);
	},
	customer_provided: function(frm, cdt, cdn) {
		calculate_additional_qty(frm, cdt, cdn);
	},
	item_add: function(frm, cdt, cdn) {
		stock_balance_fetch(frm, cdt, cdn);
	},
});

/**
* Fetch stock balance for the selected item and update the child table row
* If customer_provided is checked, skip stock balance calculation
*/
function stock_balance_fetch(frm, cdt, cdn) {
	let row = locals[cdt][cdn];  
	if (!row.item) return; 
	frappe.call({
		method: "stems.stems.doctype.bill_of_quantity.bill_of_quantity.get_item_stock_balance",
		args: { item: row.item },
		callback: function(r) {
			row.stock_balance = r.message || 0;
			calculate_additional_qty(frm, cdt, cdn);
			frm.refresh_field("items"); 
		}
	});

}

/**
* Calculate additional quantity needed based on stock balance and qty
* Skip if customer_provided is checked
*/
function calculate_additional_qty(frm, cdt, cdn) {
	let row = locals[cdt][cdn];
	if  (!row.qty || row.customer_provided) {
		row.additional_quantity_needed = 0;
		frm.refresh_field("items");
		return;
	}
	let additional_quantity_needed = row.qty - (row.stock_balance || 0);
	row.additional_quantity_needed = additional_quantity_needed > 0 ? additional_quantity_needed : 0;
	frm.refresh_field("items");
}

/**
* Show a message listing items that need additional stock.
*/
function show_additional_stock_message(frm) {
	let list = [];
	(frm.doc.items || []).forEach(row => {
		if (row.additional_quantity_needed > 0) {
			list.push(`<b>${row.item}</b>-<b>${row.additional_quantity_needed}</b>`);
		}
	});
	if (list.length) {
		let message = `Item ${list.join(', ').replace(/, ([^,]*)$/, ', $1')} more units are needed`;

		frappe.msgprint({
			message: message,
			indicator: 'orange'
		});
	}
}

/*
 * Add button to create RFQ from Bill of Quantity
 */
function add_create_rfq_button(frm) {
    // Check if any item has additional quantity needed
    let has_shortage = frm.doc.items.some(row => row.additional_quantity_needed > 0);

    if (has_shortage) {
        frm.add_custom_button("Request for Quotation", function() {
            frappe.call({
                method: "stems.stems.doctype.bill_of_quantity.bill_of_quantity.create_rfq_from_boq",
                args: { source_name: frm.doc.name },
                callback: function(r) {
                    if (r.message) {
                        frappe.set_route("Form", "Request for Quotation", r.message);
                    }
                }
            });
        }, "Create");
    }
}


// Copyright (c) 2025, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Bill of Quantity', {
	refresh: function(frm) {
		if (!frm.is_new()) {
			add_make_quotation_button(frm);
			add_create_rfq_button(frm);
		}
		if (frm.doc.project && frm.doc.docstatus === 1) {
			add_transfer_stock_button(frm);
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
* Check if item is a stock item before fetching stock balance
*/
function check_and_fetch_stock_balance(frm, cdt, cdn) {
	let row = locals[cdt][cdn];
	if (!row.item) return;

	frappe.db.get_value('Item', row.item, 'is_stock_item', (r) => {
		if (r && r.is_stock_item) {
			stock_balance_fetch(frm, cdt, cdn);
		} else {
			row.stock_balance = 0;
			row.additional_quantity_needed = 0;
			row.transferred_quantity = 0;
			frm.refresh_field("items");
		}
	});
}

/**
* Fetch stock balance for stock items
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
* Calculate additional quantity needed
*/
function calculate_additional_qty(frm, cdt, cdn) {
	let row = locals[cdt][cdn];

	if (!row.item) {
		row.additional_quantity_needed = 0;
		frm.refresh_field("items");
		return;
	}

	frappe.db.get_value('Item', row.item, 'is_stock_item', (r) => {

		if (!r || !r.is_stock_item || !row.qty || row.customer_provided) {
			row.additional_quantity_needed = 0;
		} else {

			let qty = row.qty || 0;
			let transferred_qty = row.transferred_quantity || 0;
			let stock_balance = row.stock_balance || 0;

			let remaining_qty = qty - transferred_qty;
			if (remaining_qty < 0) remaining_qty = 0;
			let shortage = remaining_qty - stock_balance;
			row.additional_quantity_needed = shortage > 0 ? shortage : 0;
		}
		frm.refresh_field("items");
	});
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
* Only show if there are stock items with shortage
*/
function add_create_rfq_button(frm) {
	let has_shortage = false;

	(frm.doc.items || []).forEach(row => {
		if (row.additional_quantity_needed > 0) {
			has_shortage = true;
		}
	});

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

/*
* Add button to transfer stock to Project Warehouse
*/
function add_transfer_stock_button(frm) {
	let has_items_to_transfer = false;

	(frm.doc.items || []).forEach(row => {
		let required_qty = (row.qty || 0) - (row.transferred_quantity || 0);
		if (!row.customer_provided && required_qty > 0) {
			has_items_to_transfer = true;
		}
	});

	if (has_items_to_transfer) {
		frm.add_custom_button(__('Transfer Stock to Project'), function() {
			transfer_stock_to_project(frm);
		});
	}
}

/**
* Create Draft Stock Entry and redirect user
* Only transfers stock items
*/
function transfer_stock_to_project(frm) {
	let items_to_check = [];

	(frm.doc.items || []).forEach(row => {
		let required_qty = (row.qty || 0) - (row.transferred_quantity || 0);
		if (!row.customer_provided && required_qty > 0 && row.item) {
			items_to_check.push(row.item);
		}
	});

	if (items_to_check.length === 0) {
		frappe.msgprint(__('All items are already transferred or customer-provided.'));
		return;
	}

	let stock_items_found = 0;
	let checks_completed = 0;

	items_to_check.forEach(item => {
		frappe.db.get_value('Item', item, 'is_stock_item', (r) => {
			checks_completed++;
			if (r && r.is_stock_item) {
				stock_items_found++;
			}

			if (checks_completed === items_to_check.length) {
				if (stock_items_found === 0) {
					frappe.msgprint(__('No stock items available to transfer.'));
					return;
				}

				frappe.call({
					method: "stems.stems.doctype.bill_of_quantity.bill_of_quantity.transfer_stock_to_project",
					args: { boq_name: frm.doc.name },
					freeze: true,
					freeze_message: __('Creating Stock Entry...'),
					callback(r) {
						if (r.message) {
							frappe.set_route("Form", "Stock Entry", r.message);
						}
					}
				});
			}
		});
	});
}

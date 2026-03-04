frappe.ui.form.on('Sales Order', {
	transaction_date: function(frm) {
		calculate_item_delivery_dates(frm);
	},
	refresh: function(frm) {
		calculate_item_delivery_dates(frm);
		allow_task_table_edit_after_submit(frm);

        if (!frm.doc.enable_percentage_invoicing) return;
		if (frm.doc.docstatus !== 1) return;

		// Remove default Create Invoice button
		frm.remove_custom_button(__('Sales Invoice'), __('Create'));

		frm.add_custom_button(__('Sales Invoice'), function () {
			open_percentage_dialog(frm);
		}, __('Create'));
	}
});

frappe.ui.form.on('Sales Order Item', {
	item_code: function(frm, cdt, cdn) {
		calculate_item_delivery_dates(frm);
	},
	items_add: function(frm) {
		calculate_item_delivery_dates(frm);
	},
	items_remove: function(frm) {
		calculate_item_delivery_dates(frm);
	}
});

frappe.ui.form.on("Task Wise Pay", {
	item(frm, cdt, cdn) {
		fetch_item_description(cdt, cdn);
	},
	percentage(frm, cdt, cdn) {
		recalculate_task_amount(frm, cdt, cdn);
	}
});

/**
 * Calculates delivery dates for items based on their task template durations.
 * Sets each item's delivery_date and updates parent delivery_date to the latest.
 */
function calculate_item_delivery_dates(frm) {
	if (!frm.doc.transaction_date || !frm.doc.items?.length) return;

	const HOURS_IN_DAY = 24;
	let parent_latest_date = null;
	let item_promises = [];

	frm.doc.items.forEach(row => {
		if (!row.item_code) return;

		let item_promise = frappe.db.get_doc('Item', row.item_code).then(item_doc => {
			let longest_days = 0;
			let task_promises = [];
			(item_doc.task_template || []).forEach(t => {
				if (!t.task_templates) return;

				let task_promise = frappe.db
					.get_doc('Task', t.task_templates)
					.then(task => {
						if (task.expected_time) {
							let days = task.expected_time / HOURS_IN_DAY;
							longest_days = Math.max(longest_days, days);
						}
					});
				task_promises.push(task_promise);
			});
			return Promise.all(task_promises).then(() => {
				if (!longest_days) return;

				let required_days = Math.ceil(longest_days);
				let delivery_date = frappe.datetime.add_days(frm.doc.transaction_date,required_days);
				frappe.model.set_value(row.doctype,row.name,"delivery_date",delivery_date);
				if (!parent_latest_date || delivery_date > parent_latest_date) {
					parent_latest_date = delivery_date;
				}
			});
		});
		item_promises.push(item_promise);
	});
	Promise.all(item_promises).then(() => {
		if (parent_latest_date) {
			frm.set_value("delivery_date", parent_latest_date);
		}
	});
}

/**
* Allow editing Task Wise Pay child table after submit
*/
function allow_task_table_edit_after_submit(frm) {
	if (frm.doc.docstatus === 1) {
		frm.set_df_property("task_wise_pay", "cannot_delete_rows", false);
	}
}

/**
 * Fetch item description from Item master
 */
function fetch_item_description(cdt, cdn) {
	let row = locals[cdt][cdn];
	if (!row.item) return;

	frappe.model.with_doc("Item", row.item, function () {
		let item_doc = frappe.get_doc("Item", row.item);
		frappe.model.set_value(
			cdt,
			cdn,
			"item_description",
			item_doc.item_name || item_doc.description || ""
		);
	});
}

/**
 * Recalculate amount based on percentage
 */
function recalculate_task_amount(frm, cdt, cdn) {
	let row = locals[cdt][cdn];
	let total = frm.doc.grand_total || 0;
	let percentage = row.percentage || 0;

	frappe.model.set_value(cdt,cdn,"amount",(total * percentage) / 100);
}


// Opens a dialog to create a percentage invoice for the sales order
function open_percentage_dialog(frm) {

	let remaining = 100 - flt(frm.doc.per_billed || 0);

	if (remaining <= 0) {
		frappe.msgprint(__("Sales Order already fully invoiced."));
		return;
	}

	frappe.call({
		method: "stems.stems.custom_scripts.sales_order.percentage_invoicing.get_so_items",
		args: { sales_order: frm.doc.name },
		callback: function (r) {

			let items = r.message || [];
			let original_items = items.slice();

			let item_fields = [
				{ fieldname: "so_detail", fieldtype: "Data", hidden: 1 },
				{ fieldname: "item_code", fieldtype: "Data", label: __("Item"), in_list_view: 1, read_only: 1 },
				{ fieldname: "item_type", fieldtype: "Data", label: __("Type"), read_only: 1 },
				{ fieldname: "uom", fieldtype: "Link", options: "UOM", label: __("UOM"), read_only: 1 },
				{ fieldname: "qty", fieldtype: "Float", label: __("Total Qty"), in_list_view: 1, read_only: 1 },
				{ fieldname: "billed_qty", fieldtype: "Float", label: __("Billed Qty"), in_list_view: 1, read_only: 1 },
				{ fieldname: "remaining_qty", fieldtype: "Float", label: __("Remaining Qty"), in_list_view: 1, read_only: 1 },
				{ fieldname: "rate", fieldtype: "Currency", label: __("Rate"), in_list_view: 1, read_only: 1 },
				{ fieldname: "total_amt", fieldtype: "Currency", label: __("Total Amt"), in_list_view: 1, read_only: 1 },
				{ fieldname: "invoiced_amount", fieldtype: "Currency", label: __("Invoiced Amount"), in_list_view: 1, read_only: 1 },
				{ fieldname: "remaining_amt", fieldtype: "Currency", label: __("Remaining Amount"), in_list_view: 1, read_only: 1 },
				{ fieldname: "percentage", fieldtype: "Float", label: __("Percentage"), in_list_view: 1 }
			];

			let d = new frappe.ui.Dialog({
				title: __("Create Percentage Invoice"),
				size: "extra-large",
				fields: [

					{
						fieldname: "percentage",
						fieldtype: "Float",
						label: __("Invoice Percentage"),
						default: remaining,
						description: __("Percentage of the order to bill in this invoice.")
					},
					{
						fieldname: "item_type_filter",
						fieldtype: "Select",
						label: __("Item Type Filter"),
						default: "All Items",
						options: [
							{ label: "Stock Items", value: "Stock Items" },
							{ label: "Service Items", value: "Service Items" },
							{ label: "All Items", value: "All Items" }
						],
						description: __("Filter items by type.")
					},
					{
						fieldname: "items",
						fieldtype: "Table",
						label: __("Items"),
						in_place_edit: true,
						data: items,
						fields: item_fields
					}
				],

				primary_action_label: __("Create Invoice"),

				primary_action(values) {

					let pct = flt(values.percentage);
					let selected = d.fields_dict.items.grid.get_selected_children();

					if (!selected.length) {
						frappe.msgprint(__("Select at least one item."));
						return;
					}

					if (!(pct > 0 && pct <= 100)) {
						frappe.msgprint(__("Enter percentage between 1 and 100."));
						return;
					}

					if (pct > remaining) {
						frappe.msgprint(__("Only {0}% remaining overall.").format(remaining));
						return;
					}

					d.hide();

					frappe.model.open_mapped_doc({
						method: "stems.stems.custom_scripts.sales_order.percentage_invoicing.make_sales_invoice_by_percentage",
						frm: frm,
						args: {
							percentage: pct,
							selected_items: selected
						}
					});
				}
			});
			d.fields_dict.item_type_filter.$input.on("change", function () {

				let selected = d.get_value("item_type_filter");
				let filtered = [];

				if (selected === "All Items") {
					filtered = original_items;
				}
				else if (selected === "Stock Items") {
					filtered = original_items.filter(row => row.item_type === "Stock");
				}
				else if (selected === "Service Items") {
					filtered = original_items.filter(row => row.item_type === "Service");
				}

				d.fields_dict.items.df.data = filtered;
				d.fields_dict.items.grid.refresh();
			});

			d.show();
		}
	});
}

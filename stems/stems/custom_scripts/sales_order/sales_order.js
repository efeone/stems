frappe.ui.form.on('Sales Order', {
	transaction_date: function(frm) {
		calculate_item_delivery_dates(frm);
	},
	refresh: function(frm) {
		calculate_item_delivery_dates(frm);
		allow_task_table_edit_after_submit(frm);

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

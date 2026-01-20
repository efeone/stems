frappe.ui.form.on('Item', {
	refresh: function(frm) {
		set_item_code_query(frm);
	}
});


/**
* Sets a filter on the Task Templates child table so that only Tasks
* with the "Is Template" checkbox enabled are available for selection.
*/
function set_item_code_query(frm) {
	frm.set_query("task_templates", "task_template", function () {
		return {
			filters: {
				is_template: 1
			}
		};
	});
}



frappe.ui.form.on('Task',{
	is_payment_required: function(frm){
		clear_check_box_exceed(frm);
	}
});

/**
* clears the "payment_percentage" field if "is_payment_required" is unchecked.
*/
function clear_check_box_exceed(frm){
	if (frm.doc.is_payment_required == 0){
		frm.set_value("payment_percentage",0);
	}
}

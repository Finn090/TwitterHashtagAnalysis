function check_box(box_id, text_id) {
	var checkBox = document.getElementById(box_id);
	var text = document.getElementById(text_id);

	if (checkBox.checked == true){
		text.style.display = "inline";
	} else {
		text.style.display = "none";
	}
}
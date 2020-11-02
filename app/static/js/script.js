function check_box(box_id, text_id) {
	var checkBox = document.getElementById(box_id);
	var text = document.getElementById(text_id);

	if (checkBox.checked == true){
		text.style.display = "inline";
	} else {
		text.style.display = "none";
	}
}

function changeHeight() {
	var height = document.getElementById("reference_1").clientHeight + document.getElementById("reference_2").clientHeight - 3;
	height = height.toString()+"px";
	document.getElementById("target").style.height = height;
}

function resizeCard() {
	var width = window.innerWidth;
	//alert(width);
}

$(document).ready(function(){
  $('[data-toggle="tooltip"]').tooltip();   
});
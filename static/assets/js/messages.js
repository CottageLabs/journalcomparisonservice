(function() {

    var dismiss_msg = document.getElementsByClassName("close");

// When the user clicks on the button, open the modal
    for (var i = 0; i < dismiss_msg.length; i++){
        dismiss_msg[i].onclick = function () {
            this.parentNode.parentNode.style.display = 'none';
        };
    }

})();

var collapsible_btn = document.getElementById("show_more");
if (collapsible_btn){
    var number = collapsible_btn.dataset.error_number;

collapsible_btn.addEventListener("click", function() {
    this.classList.toggle("active");
    var content = document.getElementsByClassName("collapsible_content");
    for (var i = 0; i < content.length; i++) {
        if (content[i].style.display === "block") {
            content[i].style.display = "none";
            collapsible_btn.innerHTML = "\u2795  Show all " + number +" errors.";
        } else {
            content[i].style.display = "block";
            collapsible_btn.innerHTML="\u2796   Show less ";
        }
    }
});
}

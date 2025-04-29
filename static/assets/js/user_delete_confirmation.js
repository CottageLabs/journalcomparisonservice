(function() {
    // Get the modal
    var modal_publisher = document.getElementById("delete_account_confirmation");
    var modal_user = document.getElementById("delete_user_confirmation");

    // Get the button that opens the modal
    var btn_publisher = document.getElementById("delete_account");
    var btn_user = document.getElementById("confirm_delete_user");

    var close_btns_publisher = document.getElementsByClassName("close_modal_publisher");
    var close_btns = document.getElementsByClassName("close_modal_user");

    if (modal_publisher) {
        for (var i = 0; i < close_btns_publisher.length; i++) {
            close_btns_publisher[i].onclick = function () {
                modal_publisher.style.display = "none";
            };
        }

        /* When the user clicks on the button, open the modal
           The logic to close modals when clicking outside the modal content box has been refactored to
           close_modals.js
        */
        btn_publisher.onclick = function () {
            modal_publisher.style.display = "block";
        };
    }

    if (modal_user) {
        for (var i = 0; i < close_btns.length; i++) {
            close_btns[i].onclick = function () {
                modal_user.style.display = "none";
            };
        }

        /* When the user clicks on the button, open the modal
           The logic to close modals when clicking outside the modal content box has been refactored to
           close_modals.js
        */

        btn_user.onclick = function () {
            modal_user.style.display = "block";
        };
    }

})();


// Delete function
document.getElementById('cancel_delete').onclick = function() { delete_modal.style.display = "none"; }
var delete_modal = document.getElementById("delete-modal");

document.getElementsByClassName("delete_link").forEach(function(del_btn) {
    del_btn.onclick = function() {
        const framework = del_btn.form.elements['delete_framework_name'].value;
        const year = del_btn.form.elements['delete_year'].value;

        document.getElementById('delete-modal-framework').innerHTML = "the " + framework + " data for the year " + year;
        document.getElementById('confirm_delete').onclick = function() { del_btn.form.submit(); }
        delete_modal.style.display = "block";

    };
});
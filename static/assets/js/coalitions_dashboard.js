(function() {
    // Get the modal
    var modal = document.getElementById("reject_confirmation");
    var modal_delete_confirmation = document.getElementById("delete_confirmation");

    // Get the button that opens the modal
    var btn = document.getElementById("deactivate_user");
    var btn_delete_user = document.getElementById("delete_user");

    var close_btns = document.getElementsByClassName("close_modal");

    if (modal) {
        for (var i = 0; i < close_btns.length; i++) {
            close_btns[i].onclick = function () {
                modal.style.display = "none";
            };
        }

        /* When the user clicks on the button, open the modal
           The logic to close modals when clicking outside the modal content box has been refactored to
           close_modals.js
        */
        btn.onclick = function () {
            modal.style.display = "block";
        };
    }

    if (modal_delete_confirmation) {
        for (var i = 0; i < close_btns.length; i++) {
            close_btns[i].onclick = function () {
                modal_delete_confirmation.style.display = "none";
            };
        }

        /* When the user clicks on the button, open the modal
           The logic to close modals when clicking outside the modal content box has been refactored to
           close_modals.js
        */
        btn_delete_user.onclick = function () {
            modal_delete_confirmation.style.display = "block";
        };
    }

    var copy_email = document.getElementById("copy_email");
    var email_copied = document.getElementById("email_copied");
    var email = document.getElementById("email");

    if (copy_email){
        copy_email.onclick = function() {
            copy_email.style.display = "none";
            navigator.clipboard.writeText(email.value);
            email_copied.style.display = "inline";
            setTimeout(function(){
                email_copied.style.display = "none";
                copy_email.style.display = "initial";
            },1500);
        };
    }

    var copy_email_esf = document.getElementById("copy_email_esf");
    var esf_email_copied = document.getElementById("esf_email_copied");
    var email_esf = document.getElementById("id_esf_email");

    if (copy_email_esf){
        copy_email_esf.onclick = function() {
            copy_email_esf.style.display = "none";
            navigator.clipboard.writeText(email_esf.value);
            esf_email_copied.style.display = "inline";
            setTimeout(function(){
                esf_email_copied.style.display = "none";
                copy_email_esf.style.display = "initial";
            },1500);
        };
    }

    var show_files_btn = document.getElementById("show_files");
    var files_list = document.getElementById("files_list");
    var details = document.getElementById("details");
    var show_user_details_btn = document.getElementById("show_user_details");

    if (show_files_btn) {
        show_files_btn.onclick = function () {
            files_list.style.display = "block";
            details.style.display = "none";
            show_files_btn.style.display = "none";
            show_user_details_btn.style.display = "block";
        };

        show_user_details_btn.onclick = function () {
            files_list.style.display = "none";
            details.style.display = "block";
            show_files_btn.style.display = "block";
            show_user_details_btn.style.display = "none";
        };
    }

})();


function myFunction() {
    var archive = document.getElementById("archive");
    var app = document.getElementById("active_users");

    if (archive.style.display === "none") {
        archive.style.display = "block";
        app.style.display = "none";

    } else {
        archive.style.display = "none";
        app.style.display = "block";
    }
}


// Delete function
document.getElementById('cancel_delete').onclick = function() { delete_modal.style.display = "none"; }
var delete_modal = document.getElementById("delete-modal");

document.getElementsByClassName("delete_link").forEach(function(del_btn) {
    del_btn.onclick = function() {
        const framework = del_btn.dataset.framework;
        const year = del_btn.dataset.year;

        document.getElementById('delete-modal-framework').innerHTML = "the " + framework + " data for the year " + year;
        document.getElementById('confirm_delete').onclick = function() { del_btn.form.submit(); }
        delete_modal.style.display = "block";

    };
});
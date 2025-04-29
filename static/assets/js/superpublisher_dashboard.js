"use strict";
(function() {

    // Get the modal
    var modal = document.getElementById("reject_confirmation");
    var modal_delete_confirmation = document.getElementById("delete_confirmation");
    var modal_promote_confirmation = document.getElementById("promote_confirmation");
    // Get the button that opens the modal
    var btn = document.getElementById("deactivate_user");
    var btn_delete_user = document.getElementById("delete_user");
    var btn_promote_user = document.getElementById("promote_user");
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

    if (modal_promote_confirmation) {
        for (var i = 0; i < close_btns.length; i++) {
            close_btns[i].onclick = function () {
                modal_promote_confirmation.style.display = "none";
            };
        }

        /* When the user clicks on the button, open the modal
           The logic to close modals when clicking outside the modal content box has been refactored to
           close_modals.js
        */
        btn_promote_user.onclick = function () {
            modal_promote_confirmation.style.display = "block";
        };

    }

  var copy_link = document.getElementById("copy_link");
  var link_copied = document.getElementById("link_copied");
  var link = document.getElementById("activation_link");

  if (copy_link){
      copy_link.onclick = function() {
          copy_link.style.display = "none";
          navigator.clipboard.writeText(link.innerText);
          link_copied.style.display = "inline";
          setTimeout(function(){
              link_copied.style.display = "none";
              copy_link.style.display = "initial";
          },1500);
      };
  }

  // Get the button that opens the modal
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

})();
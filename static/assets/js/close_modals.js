/*

There is a varied combination of ways in which modals appear in the administrative interface.

* coalitions_dashboard.js
* superpublisher_dashboard.js
* upload_verify.js
* feedback_form.js

Because the window.onclick event listener is set to hide the modal the above scripts can overlap and overwrite
each other.

For this reason it's best to set the event listener only in one place and then to hide all elements of the class
"modal".

*/

window.onclick = function(event) {
    if (Array.from(document.getElementsByClassName("modal")).indexOf(event.target) > -1) {
        event.target.style.display = "none";
    }
};
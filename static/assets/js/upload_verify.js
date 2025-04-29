
var overwrite_modal = document.getElementById("overwrite-modal");
var delete_modal = document.getElementById("delete-modal");
document.getElementById('cancel_delete').onclick = function() { delete_modal.style.display = "none"; }

var close_btns = document.getElementsByClassName("close_modal");

for (var i = 0; i < close_btns.length; i++){
  close_btns[i].onclick = function() {
    overwrite_modal.style.display = "none";
    delete_modal.style.display = "none";

  };
}

function mapFramework(f)    {
    return f.framework;
}

function submitUpload(e) {
    //const filename = e.srcElement.elements['upload_file'].files[0].name;
    var framework = e.srcElement.elements['framework'].value
    var frameworkIndex = last_years_files.map(mapFramework).indexOf(framework);

    if(frameworkIndex > -1 && overwrite_modal.style.display !== 'block') {
        // File already exists, so prompt user for confirmation of overwrite
        var frameworkObject = last_years_files[frameworkIndex];
        document.getElementById('overwrite-modal-framework').innerHTML = "the " + frameworkObject.full_name + " data for the year " + frameworkObject.year;
        overwrite_modal.style.display = "block";
        return false;
    }

    return true;
}

document.uploadform.onsubmit = submitUpload;

/* When the user clicks on the button, open the modal
   The logic to close modals when clicking outside the modal content box has been refactored to
   close_modals.js
*/

// When the user clicks on the button, open the modal

document.getElementsByClassName("delete_link").forEach(function(del_btn) {
    del_btn.onclick = function() {
        const framework = del_btn.dataset.framework;
        const year = del_btn.dataset.year;

        document.getElementById('delete-modal-framework').innerHTML = "the " + framework + " data for the year " + year;
        document.getElementById('confirm_delete').onclick = function() { del_btn.form.submit(); }
        delete_modal.style.display = "block";

    };
});
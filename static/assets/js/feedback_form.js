(function() {
    var modal = document.getElementById("feedback_form");
    // Get the button that opens the modal
    var help_btn = document.getElementById("open_feedback_form");
    var close_btn = document.getElementById("close_feedback_modal");

    close_btn.onclick = function() {
        modal.style.display = "none";
    };

    /* When the user clicks on the button, open the modal
       The logic to close modals when clicking outside the modal content box has been refactored to
       close_modals.js
    */
    help_btn.onclick = function() {
        modal.style.display = "block";
    };

})();

$(document).ready(function () {

    //  On submitting the form, send the POST ajax
    $("#feedback-form").submit(function (e) {

        // preventing from page reload and default actions
        e.preventDefault();

        // serialize the data for sending the form data.
        var serializedData = $(this).serialize();

        serializedData = serializedData + '&appCodeName='+navigator.appCodeName
            + '&appName='+navigator.appName
            + '&appVersion='+navigator.appVersion
            + '&cookieEnabled='+navigator.cookieEnabled
            + '&language='+navigator.language
            + '&platform='+navigator.platform
            + '&userAgent='+navigator.userAgent
            + '&vendor='+navigator.vendor

        // make POST ajax call
        $.ajax({
            type: 'POST',
            url: "/feedback/",
            data: serializedData,
            beforeSend: function() {
                $("#loader").show();
            },
            success: function (response) {
                $("#loader").hide();
                $("#feedback-form").trigger('reset');
                $("#feedback_sent--success").show();
                setTimeout(function() {
                    $('#feedback_sent--success').fadeOut('slow');
                }, 2000); // <-- time in milliseconds
            },

            error: function (response) {
                $("#feedback_sent--error").show();
                setTimeout(function() {
                    $('#feedback_sent--error').fadeOut('slow');
                }, 2000); // <-- time in milliseconds
            }
        })
    })
})
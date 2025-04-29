let download = {
    downloadUrl: "/dashboard/export/",  // note the trailing slash is required
    dataDump: "/dashboard/download/data_dump/",   // note the trailing slash is required

    triggerDownload: function(params) {
        let query = params.query;
        let issnsByYear = params.issns;
        let all = params.all || false;

        download.showModal((success) => {
            if (query) {
                download._triggerQueryDownload(query, success);
            } else if (issnsByYear) {
                download._triggerIssnDownload(issnsByYear, success);
            } else if (all) {
                download._triggerAllDownload(all, success);
            }
        });
    },

    showModal: function(onward) {

        let modal = `<div class="modal download_message" id="download_message">
            <div id="modal_background" class="modal-background" style="left: 25%; width: 50%; height: 60%">
                <div class="modal-content">
                    <span id="close_download_modal" class="fa fa-times close_modal"></span>
                    <div class="modal-title modal-title--warning">
                        <h3><span class="fas fa-exclamation-circle icon--error"></span>Important</h3>
                    </div>
                    <div class="modal-body" id="user-message">
                            <p>By using this Service, you acknowledge that your access to the Service is subject to complying with 
                            the applicable competition law rules. In particular, you agree that you will not, directly or 
                            indirectly, share with or make available the information provided by the Service to non-authorized 
                            persons, and in particular to publishers.</p>
                    </div>
                    <button type="submit" name="submit" id="download_data" class="btn btn-primary"><span class="fas fa-download"></span>I Agree</button>
                </div>
            </div>
        </div>`;
        $("body").append(modal);
        $("#download_message").show();

        $("#close_download_modal").on("click", function() {
            download.closeModal();
        })

        let firstClick = true;
        $(window).on("click.download_modal", function(e){
            if (firstClick) {
                firstClick = false;
                return;
            }
            if (!document.getElementById('modal_background').contains(e.target)){
                download.closeModal();
            }
        });

        $("#download_data").on("click", function() {
            onward((data) => {
                $("#user-message").html(`
                    <p>Your download request has been received. You will be emailed a link to the download file when it is ready</p>
                    <button type="submit" name="submit" id="download_requested" class="btn btn-primary">Close</button>
                `);
                $("#download_requested").on("click", function() {
                    download.closeModal();
                });
            });
            $("#download_data").prop('disabled', true);
        })
    },

    closeModal: function() {
        $("#download_message").remove();
        $(window).off("click.download_modal");
    },

    _triggerQueryDownload: function(query, success) {
        let downloadUrl = download.downloadUrl + "?query=" + encodeURIComponent(JSON.stringify(query));
        $.ajax({
            method: "get",
            url: downloadUrl,
            headers: { 'X-CSRFToken': $('input[name="csrfmiddlewaretoken"]').val() },
            success: success,
            error: function(data) {
                alert("We were unable to process your download request.  Please try again.  If the problem persists please contact us via the feedback button");
            }
        })
    },

    _triggerIssnDownload: function(issns, success) {
        $.ajax({
            method: "post",
            url: download.downloadUrl,
            headers: { 'X-CSRFToken': $('input[name="csrfmiddlewaretoken"]').val() },
            data: JSON.stringify(issns),
            contentType: "application/json",
            success: success,
            error: function(data) {
                alert("We were unable to process your download request.  Please try again.  If the problem persists please contact us via the feedback button");
            }
        })
    },

    _triggerAllDownload: function(issns, success) {
        // window.location.href = download.dataDump;
        window.open(download.dataDump);
    }
};
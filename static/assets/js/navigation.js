"use strict";
(function() {
    var users_link = document.getElementById("users_link");
    var data_link = document.getElementById("data_link");
    var settings_link = document.getElementById("settings_link");
    var user_report_link = document.getElementById("user_report_link");
    var journals_link = document.getElementById("journals_link");

    var dashboard_enpoints = ["publisher", "superpublisher", "institutionaluser", "institutionalsuperuser",
                              "journal", "comparedata", "publishers"];
    var profile_endpoint = "profile";
    var users_endpoints = ["pubnewlink", "users", "approvedusers", "awaitingusers", "archived_user",
                            "awaiting_ins_users", "approved_ins_users", "archived_ins_users"];
    var journals_end_point = "journals"
    var journal_end_point = "journal"

    var pathname = window.location.pathname;
    var pns = pathname.split("/");
    var endpoint = pns[3];

    if (users_link) {
        users_link.classList.remove("active");
    }
    if (settings_link) {
        settings_link.classList.remove("active");
    }
    if (data_link) {
        data_link.classList.remove("active");
    }
    if (user_report_link) {
        user_report_link.classList.remove("active");
    }
    if (journals_link) {
        journals_link.classList.remove("active");
    }

    if (endpoint === "") {
        endpoint = pns[2];
        if (dashboard_enpoints.includes(endpoint)){
            if (data_link) {
                data_link.classList.add("active");
            }
        }
        else if (endpoint === profile_endpoint) {
            if (settings_link) {
                settings_link.classList.add("active");
            }
        }
    }
    else if (endpoint === journals_end_point || endpoint === journal_end_point) {
        if (journals_link) {
            journals_link.classList.add("active");
        }
    }
    else if (users_endpoints.includes(endpoint)) {
        if (users_link) {
            users_link.classList.add("active");
        }
    }else if (endpoint === 'user_report'){
        if (user_report_link) {
            user_report_link.classList.add("active");
        }
    }else if (dashboard_enpoints.includes(pns[2])) {
        if (data_link) {
            data_link.classList.add("active");
        }
    }
})();
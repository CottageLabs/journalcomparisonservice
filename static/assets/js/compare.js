let compare = {

    // keyList: [],
    // rowMemory: {},

    init: function(params) {
        compare.keyList = params.keys.split(",");
        $(".js-compare--selector").on("change", compare.toggleKey);
        $(".js-toggle_rows_to_display").on("click", compare.toggleSelector);
        $(".js-toggle_select-all").on("click", compare.toggleSelectAll);
        $(".js-toggle_select-none").on("click", compare.toggleSelectNone);
    },

    toggleSelectAll: function(e) {
        e.preventDefault();
        let list = $(e.currentTarget).data("list");
        let inputs = $("#" + list).find("input")
        inputs.each(function() {
            let $this = $(this);
            $this.prop("checked", true);
            let key = $this.attr("name");
            compare.restoreRow(key);
        });
    },

    toggleSelectNone: function(e) {
        e.preventDefault();
        let list = $(e.currentTarget).data("list");
        let inputs = $("#" + list).find("input")
        inputs.each(function() {
            let $this = $(this);
            $this.prop("checked", false);
            let key = $this.attr("name");
            compare.removeRow(key);
        });
    },

    toggleSelector: function(e) {
        e.preventDefault();
        let icon = $(e.target).find("i");
        $("#rows_to_display_selector").slideToggle();

        if (icon.hasClass("fa-chevron-down")) {
            icon.removeClass("fa-chevron-down");
            icon.addClass("fa-chevron-up");
        } else {
            icon.removeClass("fa-chevron-up");
            icon.addClass("fa-chevron-down");
        }
    },

    toggleKey: function(e) {
        e.preventDefault();
        let selector = $(e.target);
        let key = selector.attr("name");
        if (selector.is(":checked")) {
            compare.restoreRow(key);
        } else {
            compare.removeRow(key);
        }
    },

    restoreRow: function(key) {
        let row = $("#" + key);
        row.removeClass("hidden");
        row.show();
    },

    removeRow: function(key) {
        let row = $("#" + key)
        row.addClass("hidden");
        row.hide();
    }
};
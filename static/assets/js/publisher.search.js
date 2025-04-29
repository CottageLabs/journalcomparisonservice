let search = {
    journalAutocompleteUrl: "/publisher_ac/journal/{prefix}",
    disciplineAutocompleteUrl: "/publisher_ac/discipline/{prefix}",

    activeEdges: {},

    valueCache : {
        "issn.raw" : {}
    },

    init: function (params) {
        let e = edges.newEdge({
            selector: "#publisher_journal_search",
            template: search.newSearchTemplate(),
            search_url: "/publisher_query",
            manageUrl: false,
            datatype: "json",
            baseQuery: es.newQuery({
                size: 20,
                sort: [{"field":"journal_title.raw", "order": "asc"}]
            }),
            components: [
                edges.newAddFieldTextFilter({
                    id: "filter-add",
                    category: "filter",
                    renderer: edges.html5.newAddFieldFilterWithCLInput({
                        logState: false,
                        fields: [
                            {field: "issn.raw", display: "Journal title"},
                            {field: "discipline.raw", display: "Discipline"}
                        ],
                        clcfgs: {
                            "issn.raw": {
                                optionsFunction: clinput.options.inputLimits({
                                    minTextLength: 3,
                                    optionsLimit: 10,
                                    inner: function (text, callback) {
                                        let url = search.journalAutocompleteUrl.replace("{prefix}", text);
                                        $.ajax({
                                            method: "get",
                                            url: url,
                                            datatype: "json",
                                            success: function(data) {
                                                callback(data);
                                            }
                                        })
                                    }
                                }),
                                optionsTemplate: function(obj) {
                                    return `${obj.title} (${obj.issn})`;
                                },
                                selectedTemplate: function(obj) {
                                    return `${obj.title} (${obj.issn})`;
                                },
                                textFromObject: function(obj) {
                                    return obj.issn;
                                }
                            },
                            "discipline.raw": {
                                optionsFunction: clinput.options.inputLimits({
                                    minTextLength: 3,
                                    optionsLimit: 3,
                                    inner: function (text, callback) {
                                        let url = search.disciplineAutocompleteUrl.replace("{prefix}", text);
                                        $.ajax({
                                            method: "get",
                                            url: url,
                                            datatype: "json",
                                            success: function (data) {
                                                callback(data);
                                            }
                                        })
                                    }
                                })
                            }
                        }
                    })
                }),
                edges.newSelectedFilters({
                    id: "selected-filters",
                    category: "filter",
                    fieldDisplays: {
                        "issn.raw": "<span>Any of the <b>Journal Titles</b></span>",
                        "discipline.raw": "<span>Any of the <b>Disciplines</b></span>"
                    },
                    ignoreUnknownFilters: true,
                    renderer: edges.pstf.newSelectedFiltersRenderer({
                        removeLinkText: "<span class='fa fa-times' id='remove_filter'></span>",
                        fieldOrder: ["issn.raw", "discipline.raw"],
                        valueFunctions: {
                            "issn.raw" : function(def, callback) {
                                var pg = edges.newAsyncGroup({
                                    list: def.values,
                                    action: function(params) {
                                        var val = params.entry;
                                        var success = params.success_callback;
                                        var error = params.error_callback;

                                        // first check the cache
                                        if (val.val in search.valueCache["issn.raw"]) {
                                            let data = search.valueCache["issn.raw"][val.val]
                                            success([data]);
                                            return;
                                        }

                                        let url = search.journalAutocompleteUrl.replace("{prefix}", val.val);
                                        $.ajax({
                                            method: "get",
                                            url: url,
                                            datatype: "json",
                                            success: success,
                                            error: error
                                        })
                                    },
                                    successCallbackArgs: ["data"],
                                    success: function(params) {
                                        var data = params.data;
                                        var val = params.entry;

                                        if (data.length === 0) {
                                            // nothing to do I don't think
                                        } else {
                                            val.display = `${data[0].title} (${data[0].issn})`;
                                            search.valueCache["issn.raw"][val.val] = data[0];
                                        }
                                    },
                                    errorCallbackArgs : ["data"],
                                    error:  function(params) {
                                        alert("Unable to retrieve data from server, please try again")
                                    },
                                    carryOn: function() {
                                        callback(def);
                                    }
                                });

                                pg.process();
                            }
                        }
                    })
                }),
                edges.newResultsDisplay({
                    id: "results",
                    category: "results",
                    renderer: search.newResultsView({})
                }),
                edges.newPager({
                    id: "bottom-pager",
                    renderer: edges.bs3.newPagerRenderer({
                        showSizeSelector: false,
                        numberFormat: edges.numFormat({
                            thousandsSeparator: ","
                        }),
                        scroll: false
                    })
                })
            ],
            callbacks: {
                "edges:query-fail": function () {
                    alert("There was an unexpected error.  Please reload the page and try again.  If the issue persists please contact us.");
                }
            }
        });
        search.activeEdges["#inst_user_search"] = e;
    },

    newSearchTemplate: function (params) {
        return edges.instantiate(search.SearchTemplate, params, edges.newTemplate);
    },
    SearchTemplate: function (params) {
        this.namespace = "pstf-search";

        this.draw = function (edge) {
            this.edge = edge;

            let clearClass = edges.css_classes(this.namespace, "clear");

            let frag = `
                <div class="row">
                    <div class="col-md-12 search--info">
                        <p>The results presented below are indicative of how users of your data will see your journals.</p>
                        <p>Recent uploads will appear in the search within a day, once they have been processed by the system.</p>
                    </div>
                </div>
                <div class="row block_filters">
                    <div class="col block shaded">
                        <h3>Narrow your results</h3>
                        <div id="filter-add"></div>
                    </div>
                </div>`

                frag += `<div id="selected-filters"></div>
                        </div>
                    </div>
                </div>`
                ;
                frag += `<div class="row gx-5">
                    <div class="col col-md-12 block shaded">
                        <div id="results"></div>
                        <div id="bottom-pager"></div>
                    </div>
                </div>`;

            this.edge.context.html(frag);
        }
    },

    newResultsView: function (params) {
        return edges.instantiate(search.ResultsView, params, edges.newRenderer)
    },
    ResultsView: function (params) {

        this.namespace = "pstf-results";

        // what to display when there are no results
        this.noResultsText = params.noResultsText || "No results to display";

        this.titleClass = edges.css_classes(this.namespace, "title", this);
        this.frameworkClass = edges.css_classes(this.namespace, "framework", this);

        this.frameworkTitles = {
            "ip": "Data for this journal was supplied using the Information Power framework",
            "foaa": "Data for this journal was supplied using the Fair Open Access Alliance framework"
        }

        this.draw = function () {
            let frag = this.noResultsText;
            if (this.component.results === false) {
                frag = "";
            }

            let results = this.component.results;
            if (results && results.length > 0) {
                frag = `
                    <table class="documents">
                        <tr>
                            <th>
                                <h3>All Journals</h3>
                            </th>
                        </tr>`;
                for (let i = 0; i < results.length; i++) {
                    frag += this._renderResult(results[i]);
                }
                frag += "</table>";
            }

            // finally stick it all together into the container
            let containerClasses = edges.css_classes(this.namespace, "container", this);
            let container = '<div class="' + containerClasses + '">' + frag + '</div>';
            this.component.context.html(container);
        }

        this._renderResult = function (record) {
            let frag = `<tr><td>
                <div class="info">
                    <h4 class="${this.titleClass} primary"><a href="/dashboard/publisher/journal/${record.issn}/${record.year}">${record.journal_title}</a></h4>
                    <p>Publisher: ${record.publisher}<br/>
                    ISSN: ${record.issn}<br/>
                    Discipline: ${record.discipline}<br/>
                    Reporting Year: ${record.year}</p>
                    <div class="tag tag--${record.framework} ${this.frameworkClass} ${record.framework}" title="${this.frameworkTitles[record.framework]}">${record.framework}</div>
                </div>
            </td></tr>`;

            return frag;
        }
    }

}
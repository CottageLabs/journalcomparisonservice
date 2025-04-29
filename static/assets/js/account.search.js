let accountSearch = {

    activeEdges: {},

    init: function (params) {
        // ensure ajax requests are not cached
        $.ajaxSetup({cache: false});

        let e = edges.newEdge({
            selector: "#account_search",
            template: edges.bs3.newFacetview(), //accountSearch.newSearchTemplate(),
            search_url: "/api/search", // set this to the correct endpoint
            queryAdapter: accountSearch.newJCSQueryAdapter(),
            manageUrl: false,
            datatype: "json",
            openingQuery: es.newQuery({
                size: 25,
                sort: [{"field":"application_date", "order": "desc"}],
                must: [new es.newTermFilter({field: "workflow_status", value: "pending"})]
            }),
            components: [
                edges.newFullSearchController({
                    id: "search_controller",
                    category: "controller",
                    sortOptions: [{ field: 'account_name', dir: "asc", display: 'Account Name'},
                    { field: 'application_date', dir: "asc", display: 'Application Date'}],
                    renderer: edges.bs3.newFullSearchControllerRenderer({
                        searchButton: true,
                        searchPlaceholder: "search accounts",
                        freetextSubmitDelay: -1,
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "user_type",
                    category: "facet",
                    orderBy: "key",
                    orderDir: "asc",
                    display: "User Type",
                    field: "user_type",
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        open: true,
                        controls: false
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "workflow_status",
                    category: "facet",
                    orderBy: "key",
                    orderDir: "asc",
                    display: "Workflow Status",
                    field: "workflow_status",
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        open: true,
                        controls: false
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "data_years",
                    category: "facet",
                    orderBy: "key",
                    orderDir: "asc",
                    display: "Data Years",
                    field: "data_years",
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        open: true,
                        controls: false
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "framework",
                    category: "facet",
                    orderBy: "key",
                    orderDir: "asc",
                    display: "Framework",
                    field: "framework",
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        open: true,
                        controls: false
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "has_uploads",
                    category: "facet",
                    orderBy: "key",
                    orderDir: "asc",
                    display: "Has Uploads",
                    field: "has_uploaded_data",
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        open: true,
                        controls: false
                    })
                }),
                edges.newSelectedFilters({
                    id: "selected-filters",
                    category: "selected-filters",
                    fieldDisplays: {
                        "workflow_status": "Workflow Status",
                        "user_type": "User Type",
                        "has_uploaded_data": "Has Uploads",
                        "data_years": "Data Years",
                        "framework": "Framework"
                    },
                    valueMaps: {"has_uploaded_data": {"has_uploads": "Yes"}},
                    ignoreUnknownFilters: true,
                    renderer: edges.bs3.newSelectedFiltersRenderer({
                    })
                }),
                edges.newResultsDisplay({
                    id: "results",
                    category: "results",
                    renderer: accountSearch.newResultsView({})
                }),
                edges.newPager({
                    id: "bottom-pager",
                    category: "bottom-pager",
                    renderer: edges.bs3.newPagerRenderer({
                        showSizeSelector: true,
                        numberFormat: edges.numFormat({
                            thousandsSeparator: ","
                        }),
                        scroll: false
                    })
                }),
                edges.newPager({
                    id: "top-pager",
                    category: "top-pager",
                    renderer: edges.bs3.newPagerRenderer({
                        showSizeSelector: true,
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
        accountSearch.activeEdges["#account_search"] = e;
    },

    newSearchTemplate: function (params) {
        return edges.instantiate(accountSearch.SearchTemplate, params, edges.newTemplate);
    },
    SearchTemplate: function (params) {
        this.namespace = "pstf-account-search";

        this.draw = function (edge) {
            this.edge = edge;

            let clearClass = edges.css_classes(this.namespace, "clear");

            let frag = ``

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
        return edges.instantiate(accountSearch.ResultsView, params, edges.newRenderer)
    },
    ResultsView: function (params) {

        this.namespace = "pstf-results";

        // what to display when there are no results
        this.noResultsText = params.noResultsText || "No results to display";

        this.titleClass = edges.css_classes(this.namespace, "title", this);

        this.draw = function () {
            let frag = this.noResultsText;
            if (this.component.results === false) {
                frag = "";
            }

            let results = this.component.results;
            if (results && results.length > 0) {
                frag = `
                    <table class="documents">
                    `;
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
            let begin_frag = `<tr><td>
                <div class="info">
                    <h4 class="${this.titleClass} primary">${record.name}</h4>
                    <ul>
                        <li>name: ${record.username}</li>
                        <li>email: ${record.email}</li>
                        <li>application date: ${record.application_submitted}</li>
                        <li>status: ${record.workflow_status}</li>`;
            if (record.is_publisher) {
                if (record.has_uploaded_data) {
                    begin_frag += `<li>data years: <ul>`
                    for (let i = 0; i < record.upload_years.length; i++) {
                            begin_frag += `<li>year: ${record.upload_years[i].year} framework: ${record.upload_years[i].framework}</li>`
                    }
                    begin_frag += `</ul></li><li>framework: ${record.framework}</li>`
                }
                else {
                    begin_frag += `<li>data years: NA</li><li>framework: NA</li>`
                }
            };
            let end_frag = `</ul>
                </div>
            </td></tr>`;

            return begin_frag + end_frag;
        }
    },

    newJCSQueryAdapter : function(params) {
        if (!params) { params = {} }
        return edges.instantiate(accountSearch.JCSQueryAdapter, params);
    },
    JCSQueryAdapter : function(params) {
        // Content of this class is copied from a project which used Invenio's API, so the model
        // here should be almost identical, and it's just the details that need to change

        this.escapeQueryString = edges.getParam(params.escapeQueryString, true);

        this.doQuery = function(params) {
            var edge = params.edge;
            var query = params.query;
            var success = params.success;
            var error = params.error;

            if (!query) {
                query = edge.currentQuery;
            }
            var args = this._es2JCS({query: query});
            this._invenioQuery({edge: edge, success: success, error: error, invenioArgs: args});
        };

        this._invenioQuery = function(params) {
            var invenioArgs = params.invenioArgs;
            var edge = params.edge;
            var success = params.success;
            var error = params.error;

            var url = this._args2URL({base_url: edge.search_url, args: invenioArgs});

            $.get({
                url: url,
                datatype: edge.datatype,
                success: es.querySuccess(success),
                error: es.queryError(error)
            })
        };

        this._args2URL = function(params) {
            var base_url = params.base_url;
            var args = params.args;

            var qParts = [];
            for (var k in args) {
                var v = args[k];
                if (Array.isArray(v)) {
                    for (var i = 0; i < v.length; i++) {
                        qParts.push(encodeURIComponent(k) + "=" + encodeURIComponent(v[i]));
                    }
                } else {
                    if (v) {
                        qParts.push(encodeURIComponent(k) + "=" + encodeURIComponent(v));
                    }
                }
            }

            var qs = qParts.join("&");
            return base_url + "?" + qs;
        };

        this._es2JCS = function(params) {
            var query = params.query;

            // get the basic properties out of the query object
            var qFrom = query.from || 0;
            var qSize = query.size === false ? 10 : query.size;
            var qQ = query.getQueryString() === false ? "" : query.getQueryString();
            var qSort = query.getSortBy().length === 0 ? false : query.getSortBy()[0];

            // convert these properties to invenio3 query properties
            var iPage = (qFrom / qSize) + 1;
            var iSize = qSize;
            var iQ = "";
            if (qQ !== "") {
                iQ = this.escapeQueryString ? qQ._escape(qQ.queryString) : qQ.queryString;
            }
            var iSort = qSort === false ? false : qSort.field;

            var iSortDir = qSort === false ? false : qSort.order;

            var iFilters = {};
            var musts = query.listMust();
            for (var i = 0; i < musts.length; i++) {
                var must = musts[i];
                if (must.type_name === "term") {
                    var field = must.field;
                    var val = must.value;
                    if (!(field in iFilters)) {
                        iFilters[field] = [];
                    }
                    iFilters[field].push(val);
                } else if (must.type_name === "terms") {
                    var field = must.field;
                    var val = must.values;
                    if (!(field in iFilters)) {
                        iFilters[field] = [];
                    }
                    iFilters[field] = iFilters[field].concat(val);
                }
            }

            var args = {
                page: iPage,
                page_size: iSize,
                q: iQ,
                sort: iSort,
                sort_dir: iSortDir,
            };
            $.extend(args, iFilters);
            return args;
        };
    },

}
let search = {
    journalAutocompleteUrl: "/autocomplete/journal/{prefix}",
    publisherAutocompleteUrl: "/autocomplete/publisher/{prefix}",
    yearAutocompleteUrl: "/autocomplete/year/{prefix}",
    publisherLookupUrl: "/pubinfo/{prefix}",
    disciplineAutocompleteUrl: "/autocomplete/discipline/{prefix}",
    compareUrl: "/dashboard/comparedata/",

    activeEdges : {},

    valueCache : {
        "issn.raw" : {},
        "publisher_id": {}
    },

    init: function(params) {

        // ensure ajax requests are not cached
        $.ajaxSetup({cache: false});

        $("#download-by-issn").click(function(){
            $("#download-by-issn-content").toggle();
        });

        let e = edges.newEdge({
            selector: "#inst_user_search",
            template: search.newSearchTemplate(),
            search_url: "/search",
            manageUrl : true,
            datatype: "json",
            baseQuery: es.newQuery({
                size: 20,
                sort: [{"field":"journal_title.raw", "order": "asc"}]
            }),
            components : [
                edges.newAddFieldTextFilter({
                    id: "filter-add",
                    category: "filter",
                    renderer: edges.html5.newAddFieldFilterWithCLInput({
                        logState: false,
                        fields: [
                            {field: "issn.raw", display: "Journal title"},
                            {field: "publisher_id", display: "Publisher"},
                            {field: "discipline.raw", display: "Discipline"},
                            {field: "year", display: "Year"}
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
                            "publisher_id": {
                                optionsFunction: clinput.options.inputLimits({
                                    minTextLength: 3,
                                    optionsLimit: 10,
                                    inner: function (text, callback) {
                                        let url = search.publisherAutocompleteUrl.replace("{prefix}", text);
                                        $.ajax({
                                            method: "get",
                                            url: url,
                                            datatype: "json",
                                            success: function (data) {
                                                callback(data);
                                            }
                                        })
                                    }
                                }),
                                optionsTemplate: function(obj) {
                                    let country = "";
                                    if (obj.country) {
                                        country = ` (${obj.country})`;
                                    }
                                    return `${obj.name}${country}`;
                                },
                                selectedTemplate: function(obj) {
                                    let country = "";
                                    if (obj.country) {
                                        country = ` (${obj.country})`;
                                    }
                                    return `${obj.name}${country}`;
                                },
                                textFromObject: function(obj) {
                                    return obj.id;
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
                            },
                            "year": {
                                optionsFunction: clinput.options.inputLimits({
                                    minTextLength: -1,
                                    optionsLimit: 10,
                                    inner: function (text, callback) {
                                        let url = search.yearAutocompleteUrl.replace("{prefix}", text);
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
                        "publisher_id": "<span>Any of the <b>Publishers</b></span>",
                        "discipline.raw": "<span>Any of the <b>Disciplines</b></span>",
                        "year": "<span>Any of the <b>Years</b></span>"
                    },
                    ignoreUnknownFilters: true,
                    renderer: edges.pstf.newSelectedFiltersRenderer({
                        removeLinkText: "<span class='fa fa-times' id='remove_filter'></span>",
                        fieldOrder: ["issn.raw", "publisher_id", "discipline.raw", "year"],
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
                            },
                            "publisher_id": function(def, callback) {
                                var pg = edges.newAsyncGroup({
                                    list: def.values,
                                    action: function(params) {
                                        var val = params.entry;
                                        var success = params.success_callback;
                                        var error = params.error_callback;

                                        // first check the cache
                                        if (val.val in search.valueCache["publisher_id"]) {
                                            let data = search.valueCache["publisher_id"][val.val]
                                            success(data);
                                            return;
                                        }

                                        let url = search.publisherLookupUrl.replace("{prefix}", val.val);
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

                                        let country = "";
                                        if (data.country) {
                                            country = ` (${data.country})`;
                                        }
                                        val.display = `${data.name}${country}`;
                                        search.valueCache["publisher_id"][val.val] = data;
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
                        },
                        parseValueFromString: {
                            "publisher_id": function(val) {
                                return parseInt(val);
                            },
                            "year": function(val) {
                                return parseInt(val);
                            }
                        }
                    })
                }),
                edges.newResultsDisplay({
                    id: "results",
                    category: "results",
                    renderer: search.newResultsView({

                    })
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
                }),
                search.newShoppingBasket({
                    id: "shopping-basket",
                    compareUrl: search.compareUrl
                })
            ],
            callbacks : {
                "edges:query-fail" : function() {
                    alert("There was an unexpected error.  Please reload the page and try again.  If the issue persists please contact us.");
                }
            }
        });
        search.activeEdges["#inst_user_search"] = e;
    },

    newSearchTemplate : function(params) {
        return edges.instantiate(search.SearchTemplate, params, edges.newTemplate);
    },
    SearchTemplate : function(params) {
        this.namespace = "pstf-search";

        this.draw = function(edge) {
            this.edge = edge;

            let clearClass = edges.css_classes(this.namespace, "clear");

            let frag = `
                <div class="col">
                    <div class="row block_filters">
                        <div class="col">
                            <div class="block shaded">
                                <h3>Narrow your results</h3>
                                <div id="filter-add"></div>
                            </div>
                        </div>
                        <div class="block selected-filters" id="selected-filters" ></div>
                    </div>
                    <div class="row">
                        <div class="col">
                            <div class="block shaded" id="results"></div>
                            <div class="block shaded" id="bottom-pager"></div>
                        </div>
                        <div class="col">
                            <div class="block shaded" id="shopping-basket"></div>
                        </div>
                    </div>
                </div>`
            ;

            this.edge.context.html(frag);
        }
    },

    newResultsView : function(params) {
        return edges.instantiate(search.ResultsView, params, edges.newRenderer)
    },
    ResultsView: function(params) {

        this.shoppingBasketId = edges.getParam(this.shoppingBasketId, "shopping-basket")

        this.namespace = "pstf-results";

        // what to display when there are no results
        this.noResultsText = params.noResultsText || "No results to display";

        this.addClass = edges.css_classes(this.namespace, "add", this);
        this.removeClass = edges.css_classes(this.namespace, "remove", this);
        this.titleClass = edges.css_classes(this.namespace, "title", this);
        this.frameworkClass = edges.css_classes(this.namespace, "framework", this);

        this.addIcon = "fa-plus";
        this.removeIcon = "fa-minus";
        this.addTitle = "Add journal to your selection";
        this.removeTitle = "Remove journal from your selection";
        this.addSelector = edges.css_class_selector(this.namespace, "add", this);
        this.removeSelector = edges.css_class_selector(this.namespace, "remove", this);

        this.frameworkTitles = {
            "ip" : "Data for this journal was supplied using the Information Power framework",
            "foaa": "Data for this journal was supplied using the Fair Open Access Alliance framework"
        }

        this.basket = false;

        this.init = function(component) {
            edges.up(this, "init", [component]);
            this.basket = this.component.edge.getComponent({id: this.shoppingBasketId});
        }

        this.draw = function() {
            let frag = this.noResultsText;
            if (this.component.results === false) {
                frag = "";
            }

            let results_non_sorted = this.component.results;
            if (results_non_sorted && results_non_sorted.length > 0) {

                let _compare = function(a,b) {
                    if (a.journal_title < b.journal_title) {
                        return -1;
                    }
                    else if (a.journal_title > b.journal_title) {
                        return 1;
                    }
                    return 0;
                };

                let results = results_non_sorted.sort(_compare);
                // list the css classes we'll require
                let recordClasses = edges.css_classes(this.namespace, "record", this);
                let addAllClass = edges.css_classes(this.namespace, "addall", this);

                // now call the result renderer on each result to build the records
                let addAllFrag = ""
                if (this.component.edge.result.total() > 0) {
                    addAllFrag = `<a href="#" class="${addAllClass}" style="text-decoration: none"><i class="fa fa-download" aria-label="Download current search results"></i> <span id="download-all-text">Download current search results</span></a>`;
                }
                frag = `
                    <table class="documents">
                        <tr>
                            <th>
                                <h3>Matching journals (${this.component.hitCount})</h3>
                                ${addAllFrag}
                            </th>
                        </tr>`;
                for (let i = 0; i < results.length; i++) {
                    frag += this._renderResult(results[i]);
                }
                frag +="</table>";
            }

            // finally stick it all together into the container
            let containerClasses = edges.css_classes(this.namespace, "container", this);
            let container = '<div class="' + containerClasses + '">' + frag + '</div>';
            this.component.context.html(container);

            this.bindAddRemove();

            let addAllSelector = edges.css_class_selector(this.namespace, "addall", this);
            edges.on(addAllSelector, "click", this, "downloadQueryClicked");
        }

        this._renderResult = function(record) {
            let recordData = encodeURIComponent(JSON.stringify(record));

            let actionClass = this.addClass;
            let actionIcon = this.addIcon;
            let actionTitle = this.addTitle;
            if (this.basket.inBasket(record.issn, record.year) > -1) {
                actionClass = this.removeClass
                actionIcon = this.removeIcon;
                actionTitle = this.removeTitle;
            }

            let frag = `<tr><td class="journal">
                <span aria-label="add journal to your selection" class="${actionClass} add_link fas ${actionIcon}" data-record="${recordData}" title="${actionTitle}" style="padding-right: 20px;"></span>
                <div class="info">
                    <h4 class="${this.titleClass}"><a href="/dashboard/journal/${record.issn}/${record.year}">${record.journal_title}</a></h4>
                    <p>Publisher: ${record.publisher}<br/>
                    ISSN: ${record.issn}<br/>
                    Discipline: ${record.discipline}<br/>
                    Reporting Year: ${record.year}</p>
                    <div class="tag tag--${record.framework} ${this.frameworkClass} ${record.framework}" title="${this.frameworkTitles[record.framework]}">${record.framework}</div>
                </div>
            </td></tr>`;

            return frag;
        }

        this.addToBasket = function(element) {
            let el = $(element);
            let record = JSON.parse(decodeURIComponent(el.attr("data-record")));
            this.basket.addRecord(record);

            el.removeClass(this.addIcon);
            el.removeClass(this.addClass);
            el.addClass(this.removeClass);
            el.addClass(this.removeIcon);
            el.attr("title", this.removeTitle);

            this.bindAddRemove();
        }

        this.removeFromBasket = function(element) {
            let el = $(element);
            let record = JSON.parse(decodeURIComponent(el.attr("data-record")));
            this.basket.removeRecord(record.issn, record.year);

            el.removeClass(this.removeIcon);
            el.removeClass(this.removeClass);
            el.addClass(this.addClass);
            el.addClass(this.addIcon);
            el.attr("title", this.addTitle);

            this.bindAddRemove();
        }

        this.downloadQueryClicked = function(element) {
            download.triggerDownload({
                query: this.component.edge.currentQuery.objectify()
            })
        }

        this.bindAddRemove = function() {
            edges.on(this.addSelector, "click", this, "addToBasket");
            edges.on(this.removeSelector, "click", this, "removeFromBasket");
        }
    },

    newShoppingBasket: function(params) {
        return edges.instantiate(search.ShoppingBasket, params, edges.newComponent)
    },
    ShoppingBasket: function(params) {

        this.emptyBasketText = edges.getParam(params.emptyBasketText, "No journals selected yet");

        this.resultsComponentId = edges.getParam(params.resultsComponentId, "results");

        this.compareUrl = edges.getParam(params.compareUrl, "/compare");
        this.pageSize = edges.getParam(params.pageSize, 25);

        this.namespace = "pstf-basket"

        this.basket = [];

        this.component = this;

        this.removeClass = edges.css_classes(this.namespace, "remove", this);
        this.titleClass = edges.css_classes(this.namespace, "title", this);
        this.frameworkClass = edges.css_classes(this.namespace, "framework", this);

        this.removeSelector = edges.css_class_selector(this.namespace, "remove", this);

        this.frameworkTitles = {
            "ip" : "Data for this journal was supplied using the Information Power framework",
            "foaa": "Data for this journal was supplied using the Fair Open Access Alliance framework"
        }

        this.addRecord = function(record) {
            let issn = record.issn;
            let year = record.year;
            if (this.inBasket(issn, year) > -1) {
                return;
            }

            this.basket.push(record);

            this.draw();
        }

        this.removeRecord = function(issn, year) {
            let idx = this.inBasket(issn, year);
            if (idx === -1) {
                return;
            }

            this.basket.splice(idx, 1);

            this.draw();
        }

        this.inBasket = function(issn, year) {
            for (let i = 0; i < this.basket.length; i++) {
                let r = this.basket[i];
                if (r.issn === issn && r.year === year) {
                    return i;
                }
            }
            return -1;
        }

        this.removeFromBasket = function(element) {
            let el = $(element);
            let issn = el.attr("data-issn");
            let year = el.attr("data-year");
            this.removeRecord(issn, parseInt(year));

            // FIXME: slightly lazy way of doing this, should probably emit and listen for an event
            let results = this.edge.getComponent({id: this.resultsComponentId});
            results.draw();
        }

        this.emptyBasket = function(element) {
            let sure = confirm("Are you sure you want to remove all the items from your selected list?");
            if (!sure) {
                return;
            }

            this.basket = [];
            this.draw();

            // FIXME: slightly lazy way of doing this, should probably emit and listen for an event
            let results = this.edge.getComponent({id: this.resultsComponentId});
            results.draw();
        }

        this.draw = function() {
            let frag = this.emptyBasketText;
            let compareFrag = "Select between 2 and 5 journals to compare";
            let downloadFrag = "Select one or more journals to download";

            // list the css classes we'll require
            let recordClasses = edges.css_classes(this.namespace, "record", this);
            let removeAllClass = edges.css_classes(this.namespace, "removeall", this);

            let removeAll = `<span href="#" class="${removeAllClass} fa fa-minus" title="Remove all journals from selection"></span> `;

            frag = `
                    <table class="documents">
                        <tr>
                            <th>
                                <h3>${removeAll}&nbsp;&nbsp;Your chosen journals</h3>
                            </th>
                        </tr>`;
            if (this.basket.length === 0) {
                frag += `<tr><td class="disabled"><div class="info"><h5>Select journals to compare or download</h5></div></td></tr>`
            }
            else {
                for (let i = 0; i < this.basket.length; i++) {
                    frag += this._renderResult(this.basket[i]);
                }
            }
            frag +=`</table>`;

            let downloadClass = edges.css_classes(this.namespace, "download", this);
            if (this.basket.length > 0) {
                frag += `<button type="button" class="btn btn-primary ${downloadClass}"><span class="fas fa-download"></span>Download selected journals</button>`
            }

            if (this.basket.length > 1 && this.basket.length <= 5) {
                let issns = '[';
                for (let i = 0; i < this.basket.length; i++) {
                    let r = this.basket[i];
                    if(issns.length > 1){
                        issns += ','
                    }
                    issns += '{%22issn%22: %22'+ r.issn +'%22, %22year%22: ' + r.year + '}'
                }
                issns += ']';

                let compareLink = this.compareUrl + issns + "/";
                frag += `<a href="${compareLink}" class="btn btn-primary"><span class="fas fa-exchange-alt"></span>Compare in the browser (max 5)</a>`;
            }

            if (this.basket.length > 5) {
                frag += `<button class="btn btn-primary" disabled><span class="fas fa-exchange-alt"></span>You cannot compare more than 5 journals in the browser</button>`;
            }

            // finally stick it all together into the container
            let containerClasses = edges.css_classes(this.namespace, "container", this);
            let container = '<div class="' + containerClasses + '">' + frag + '</div>';
            this.component.context.html(container);

            this.bindRemove();

            let removeAllSelector = edges.css_class_selector(this.namespace, "removeall", this);
            edges.on(removeAllSelector, "click", this, "emptyBasket");

            let downloadSelector = edges.css_class_selector(this.namespace, "download", this);
            edges.on(downloadSelector, "click", this, "download");
        }

        this._renderResult = function(record) {

            let frag = `<tr><td class="journal">
                <span aria-label="remove journal from selection" class="${this.removeClass} add_link fas fa-minus" data-issn="${record.issn}" data-year="${record.year}" title="Remove journal from selection" style="padding-right: 20px;"></span>
                <div class="info">
                    <h4 class="${this.titleClass}"><a href="/dashboard/journal/${record.issn}/${record.year}">${record.journal_title}</a> (${record.year})</h4>
                    <p>(ISSN ${record.issn}) ${record.publisher}; ${record.discipline}<p>
                    <div class="tag tag--${record.framework} ${this.frameworkClass} ${record.framework}" title="${this.frameworkTitles[record.framework]}">${record.framework}</div>
                </div>
            </td></tr>`;

            return frag;
        }

        this.bindRemove = function() {
            edges.on(this.removeSelector, "click", this, "removeFromBasket");
        }

        this.download = function() {
            let issns = []
            for (let i = 0; i < this.basket.length; i++) {
                let r = this.basket[i];
                issns.push({issn: r.issn, year: r.year})
            }
            download.triggerDownload({
                issns: issns
            })
        }
    }
};
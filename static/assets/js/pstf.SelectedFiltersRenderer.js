$.extend(true, edges, {
    pstf : {
        newSelectedFiltersRenderer: function (params) {
            return edges.instantiate(edges.pstf.SelectedFiltersRenderer, params, edges.newRenderer);
        },
        SelectedFiltersRenderer: function (params) {

            this.fieldOrder = edges.getParam(params.fieldOrder, []);

            this.removeLinkText = edges.getParam(params.removeLinkText, "X");

            this.valueFunctions = edges.getParam(params.valueFunctions, {});

            this.parseValueFromString = edges.getParam(params.parseValueFromString, {});

            this.namespace = "edges-pstf-selected-filters";

            this.draw = function () {
                // for convenient short references
                var sf = this.component;
                var ns = this.namespace;

                // sort out the classes we are going to use
                var fieldClass = edges.css_classes(ns, "field", this);
                var fieldNameClass = edges.css_classes(ns, "fieldname", this);
                var containerClass = edges.css_classes(ns, "container", this);

                var filters = "";

                for (var i = 0; i < this.fieldOrder.length; i++) {
                    var field = this.fieldOrder[i];
                    var def = sf.mustFilters[field];
                    if (!def) {
                        continue;
                    }

                    filters += '<div class="' + fieldClass + '">';
                    filters += '<p class="' + fieldNameClass + '">' + def.display + ':';

                    let filterValuesId = edges.css_id(this.namespace, edges.safeId(field), this);
                    filters += `<span id="${filterValuesId}">`;

                    if (field in this.valueFunctions) {
                        let timeoutFunction = function(that, f, def) {
                            let callbackClosure = function (f2) {
                                return function (nd) {
                                    that.valuesResolved(f2, nd)
                                }
                            }
                            return function() {
                                that.valueFunctions[f](def, callbackClosure(f));
                            }
                        }
                        window.setTimeout(timeoutFunction(this, field, def), 0);
                    }
                     else {
                        filters += this._renderFilterList(field, def);
                    }
                     filters += '</p></div>';
                }

                if (filters !== "") {
                    let frag = `<div class="${containerClass}">
                        <div class="row block block_filters">
                            <div class="col">
                                <div class="row">
                                    <h2>Your current search</h2>
                                    ${filters}
                                </div>
                            </div>
                        </div>
                    </div>`;

                    sf.context.html(frag);

                    // click handler for when a filter remove button is clicked
                    var removeSelector = edges.css_class_selector(ns, "remove", this);
                    edges.on(removeSelector, "click", this, "removeFilter");
                } else {
                    sf.context.html("");
                }
            };

            this.valuesResolved = function(field, def) {
                let filters = this._renderFilterList(field, def);

                let filterValuesId = edges.css_id_selector(this.namespace, edges.safeId(field), this);
                $(filterValuesId).html(filters);

                // click handler for when a filter remove button is clicked
                var removeSelector = edges.css_class_selector(this.namespace, "remove", this);
                edges.on(removeSelector, "click", this, "removeFilter");
            };

            this._renderFilterList = function (field, def) {
                let valClass = edges.css_classes(this.namespace, "value", this);
                let filters = "";

                for (var j = 0; j < def.values.length; j++) {
                    var val = def.values[j];
                    filters += '<span class="' + valClass + ' tag tag--filter">' + val.display;

                    // the remove block looks different, depending on the kind of filter to remove
                    var removeClass = edges.css_classes(this.namespace, "remove", this);
                    if (def.filter === "term" || def.filter === "terms") {
                        filters += '<a class="' + removeClass + '" data-bool="must" data-filter="' + def.filter + '" data-field="' + field + '" data-value="' + val.val + '" title="Remove" href="#">';
                        filters += this.removeLinkText;
                        filters += "</a></span>";
                    } else if (def.filter === "range") {
                        var from = val.from ? ' data-' + val.fromType + '="' + val.from + '" ' : "";
                        var to = val.to ? ' data-' + val.toType + '="' + val.to + '" ' : "";
                        filters += '<a class="' + removeClass + '" data-bool="must" data-filter="' + def.filter + '" data-field="' + field + '" ' + from + to + ' title="Remove" href="#">';
                        filters += this.removeLinkText;
                        filters += "</a>";
                    }
                }

                return filters;
            }

            /////////////////////////////////////////////////////
            // event handlers

            this.removeFilter = function (element) {
                var el = this.component.jq(element);
                var field = el.attr("data-field");
                var ft = el.attr("data-filter");
                var bool = el.attr("data-bool");

                var value = false;
                if (ft === "terms" || ft === "term") {
                    value = el.attr("data-value");
                    if (field in this.parseValueFromString) {
                        value = this.parseValueFromString[field](value);
                    }
                } else if (ft === "range") {
                    value = {};

                    var from = el.attr("data-gte");
                    var fromType = "gte";
                    if (!from) {
                        from = el.attr("data-gt");
                        fromType = "gt";
                    }

                    var to = el.attr("data-lt");
                    var toType = "lt";
                    if (!to) {
                        to = el.attr("data-lte");
                        toType = "lte";
                    }

                    if (from) {
                        value["from"] = parseInt(from);
                        value["fromType"] = fromType;
                    }
                    if (to) {
                        value["to"] = parseInt(to);
                        value["toType"] = toType;
                    }
                }

                this.component.removeFilter(bool, ft, field, value);
            };
        }
    }
});

// Non-UI filter code, for use in multiple applications.

// Global declaration for JSLint (http://www.jslint.com/)
/*global console, dojo, dojox, gobotany */

dojo.provide('gobotany.filters');
dojo.require('dojox.data.JsonRestStore');

// Filter
//
// Base for the different types of filters.
//
dojo.declare("gobotany.filters.Filter", null, {
    character_short_name: "",
    friendly_name: "",
    order: 0,
    pile_slug: "",
    value_type: "",
    selected_value: null,
    constructor: function(args) {
        this.character_short_name = args.character_short_name;
        this.friendly_name = args.friendly_name;
        this.order = args.order;
        this.pile_slug = args.pile_slug;
        this.value_type = args.value_type;
        dojo.safeMixin(this, args);
        var url = '/piles/' + this.pile_slug + '/' + 
                  this.character_short_name + '/';
        this.store = new dojox.data.JsonRestStore({target: url});
    },
    load_values: function(args) {
        if (args && args.onLoaded) {
            args.onLoaded();
        }
    }
});


// MultipleChoiceFilter
//
dojo.declare("gobotany.filters.MultipleChoiceFilter", 
             [gobotany.filters.Filter], {
    values: null,
    constructor: function(args) {
        this.values = [];
    },
    load_values: function(args) {
        this.store.fetch({
            scope: this,
            onComplete: function(response) {
                dojo.forEach(response, this.process_value, this);
                if (args && args.onLoaded) {
                    args.onLoaded();
                }
            }
        });
    },
    process_value: function(character_value, index) {
        this.values.push(character_value);
    }
});


// NumericRangeFilter
//
dojo.declare('gobotany.filters.NumericRangeFilter',
             [gobotany.filters.MultipleChoiceFilter], {
    process_value: function(character_value, index) {
        // We make this.values a one-element list: [{min: a, max: b}]
        if (this.values.length) {
            var v = this.values[0];
            if (v.min > character_value.value_min) {
                v.min = character_value.value_min;
            }
            if (v.max < character_value.value_max) {
                v.max = character_value.value_max;
            }
        } else {
            this.values = [{
                min: character_value.value_min,
                max: character_value.value_max
            }];
        }
    }
});


// FilterManager
//
// A FilterManager object is responsible for pulling a pile's filters from
// the REST API and maintaining a collection.
// It pulls a set of default filters, then later would pull more filters
// as needed.
//
dojo.declare("gobotany.filters.FilterManager", null, {
    pile_slug: "",
    character_groups: null,
    filters: null,
    species_count: 0,
    entries: [],
    constructor: function(args) {
        this.pile_slug = args.pile_slug;
        this.character_groups = [];
        this.filters = [];
        this.filters_loading = 0;

        if (!args.pile_url) args.pile_url = '/piles/';
        if (!args.taxon_url) args.taxon_url = '/taxon/';
        this.store = new dojox.data.JsonRestStore({target: args.pile_url});
        this.result_store = new dojox.data.JsonRestStore({target: args.taxon_url, 
                                                          idAttribute: 'scientific_name'});
    },
    load_default_filters: function(args) {
        var store = this.store;
        store.fetchItemByIdentity({
            scope: {args: args, filter_manager: this},
            identity: this.pile_slug,
            onItem: function(item) {

                // Save the character groups for this pile.

                this.filter_manager.character_groups = item.character_groups;

                // Start off with the default filters for this pile.

                console.log('item.default_filters.length: ' +
                            item.default_filters.length);
                this.filter_manager.filters_loading =
                    item.default_filters.length;
                console.log('this.filter_manager.filters_loading: ' +
                    this.filter_manager.filters_loading);
                for (var y = 0; y < item.default_filters.length; y++) {
                    var filter_json = item.default_filters[y];
                    this.filter_manager.add_filter({
                        filter_json: filter_json,
                        onAdded: dojo.hitch(this, 
                            this.filter_manager._watch_filters_loading)
                    });
                }
            }
        });
    },
    _watch_filters_loading: function(data) {
        // scope should be an object with filter_manager and onLoaded attrs

        this.filter_manager.filters_loading--;
        if (this.args && this.args.onLoaded && 
            this.filter_manager.filters_loading === 0) {

            this.args.onLoaded();
        }
    },
    add_filter: function(args) {
        var filter_json = args.filter_json;
        var filter_type;

        if (filter_json.value_type == 'LENGTH') {
            filter_type = gobotany.filters.NumericRangeFilter;
        }
        else if (filter_json.value_type == 'TEXT')  {
            filter_type = gobotany.filters.MultipleChoiceFilter;
        }
        else {
            filter_type = gobotany.filters.Filter;
        }

        var filter = new filter_type(
            {
                friendly_name: filter_json.character_friendly_name,
                character_short_name: filter_json.character_short_name,
                order: filter_json.order,
                notable_exceptions: filter_json.notable_exceptions,
                key_characteristics: filter_json.key_characteristics,
                value_type: filter_json.value_type,
                pile_slug: this.pile_slug
            }
        );

        // Add the filter to the manager's collection of filters.
        this.filters.push(filter);

        if (args && args.onAdded) {
            filter.load_values({onLoaded: dojo.hitch(this, function() {
                args.onAdded(filter);
            })});
        }
    },
    add_text_filters: function(filter_names) {
        for (var i = 0; i < filter_names.length; i++) {
            var filter = new gobotany.filters.Filter(
                {
                    friendly_name: '', // not needed yet
                    character_short_name: filter_names[i],
                    order: 0,
                    notable_exceptions: null,
                    key_characteristics: null,
                    value_type: null,
                    pile_slug: this.pile_slug
                }
            );
            this.filters.push(filter);
        }
    },
    set_selected_value: function(character_short_name, selected_value) {
        var found_filter = false;
        var i = 0;
        while (!found_filter && i < this.filters.length) {
            if (this.filters[i].character_short_name === 
                character_short_name) {

                this.filters[i].selected_value = selected_value;
                found_filter = true;
            }
            i++;
        }
    },
    get_selected_value: function(character_short_name) {
        var selected_value = null;
        var found_filter = false;
        var i = 0;
        while (!found_filter && i < this.filters.length) {
            if (this.filters[i].character_short_name === 
                character_short_name) {

                var value = this.filters[i].selected_value;
                if (value !== null && value.length) {
                    selected_value = value;
                }
                found_filter = true;
            }
            i++;
        }
        return selected_value;
    },
    run_filtered_query: function(onComplete) {
        var content = {pile: this.pile_slug};

        for (var i = 0; i < this.filters.length; i++) {
            var filter = this.filters[i];
            if (filter.selected_value !== null && 
                filter.selected_value.length) {

                content[filter.character_short_name] = filter.selected_value;
            }
        }
        //var content_str = '';
        //for (var key in content) {
        //    if (content.hasOwnProperty(key)) {
        //        content_str += key + ': ' + content[key] + ' ';
        //    }
        //}
        //console.log('content_str: ' + content_str);

        this.result_store.fetch({
            scope: this,
            query: content,
            onComplete: function(data) {
                this.species_count = data.items.length;

                // Call the passed-in callback function.
                onComplete(data);
            },
            onError: function(error) {
                console.log('Taxon search encountered an error!');
                console.log(error);
            }
        });
    }
});

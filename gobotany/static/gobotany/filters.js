// Non-UI filter code, for use in multiple applications.

// Global declaration for JSLint (http://www.jslint.com/)
/*global dojo, dojox, gobotany */

dojo.provide('gobotany.filters');
dojo.require('dojox.data.JsonRestStore');

// Filter
//
// Base for the different types of filters.
//
dojo.declare("gobotany.filters.Filter", null, {
    friendly_name: "",
    order: 0,
    pile_slug: "",
    value_type: "",
    constructor: function(args) {
        this.friendly_name = args.friendly_name;
        this.order = args.order;
        this.pile_slug = args.pile_slug;
        this.value_type = args.value_type;
        dojo.safeMixin(this, args);
    },
    load_values: function(args) {
        if (args && args.onLoaded)
            args.onLoaded();
    }
});


// MultipleChoiceFilter
//
dojo.declare("gobotany.filters.MultipleChoiceFilter", 
             [gobotany.filters.Filter], {
    character_short_name: "",
    values: null,
    constructor: function(args) {
        this.character_short_name = args.character_short_name;
        this.value_type = args.value_type;
        this.values = [];
        var url = '/piles/' + this.pile_slug + '/' + 
                  this.character_short_name + '/';
        this.store = new dojox.data.JsonRestStore({target: url,
                                                   syncMode: true});
    },
    load_values: function(args) {
        this.store.fetch({
            scope: this,
            onComplete: function(response) {
                dojo.forEach(response, this.process_value, this);
                if (args && args.onLoaded)
                    args.onLoaded();
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
        if (this.values.Length) {
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

// TODO: TextFilter?


// FilterManager
//
// A FilterManager object is responsible for pulling a pile's filters from
// the REST API and maintaining a collection.
// It pulls a set of default filters, then later would pull more filters
// as needed.
//
dojo.declare("gobotany.filters.FilterManager", null, {
    pile_slug: "",
    default_filters: null,
    constructor: function(args) {
        this.pile_slug = args.pile_slug;
        this.default_filters = [];
        this.filters_loading = 0;

        var url = '/piles/';
        this.store = new dojox.data.JsonRestStore({target: url});
    },
    load_default_filters: function(args) {
        var store = this.store;
        store.fetchItemByIdentity({
            scope: {args: args, filter_manager: this},
            identity: this.pile_slug,
            onItem: function(item) {
                this.filter_manager.filters_loading = item.default_filters.length;
                for (var y = 0; y < item.default_filters.length; y++) {
                    var filter_json = item.default_filters[y];
                    this.filter_manager.add_filter({
                        filter_json: filter_json,
                        onAdded: dojo.hitch(this, this.filter_manager._watch_filters_loading)
                    });
                }
            }
        });
    },
    _watch_filters_loading: function(data) {
        // scope should be an object with filter_manager and onLoaded attrs

        this.filter_manager.filters_loading--;
        if (this.args && this.args.onLoaded && this.filter_manager.filters_loading == 0)
            this.args.onLoaded();
    },
    add_filter: function(args) {
        var filter_json = args.filter_json;
        var filter_type;
        if (filter_json.value_type == 'LENGTH') {
            filter_type = gobotany.filters.NumericRangeFilter;
        }
        else {
            filter_type = gobotany.filters.MultipleChoiceFilter;
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

        // Add the filter to the manager's collection of default
        // filters.
        this.default_filters.push(filter);

        if (args && args.onAdded) {
            filter.load_values({onLoaded: dojo.hitch(this, function() {
                args.onAdded(filter);
            })});
        }
    }
});

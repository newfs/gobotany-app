// Non-UI filter code, for use in multiple applications.

dojo.provide('gobotany.filters');
dojo.require('dojox.data.JsonRestStore');

// Filter
//
// Base for the different types of filters.
//
dojo.declare("Filter", null, {
    friendly_name: "",
    order: 0,
    pile_slug: "",
    constructor: function(args) {
        this.friendly_name = args.friendly_name;
        this.order = args.order;
        this.value_type = args.value_type;
        this.pile_slug = args.pile_slug;
        dojo.safeMixin(this, args);
    }
});


// MultipleChoiceFilter
//
dojo.declare("MultipleChoiceFilter", [Filter], {
    character_short_name: "", // Only one character field needed (unlike numeric?)
    values: null,
    constructor: function(args) {
        this.character_short_name = args.character_short_name;
        this.value_type = args.value_type;
        this.values = [];
    },
    load_values: function() {
        var url = '/piles/' + this.pile_slug + '/' + 
                  this.character_short_name + '/';
        var store = new dojox.data.JsonRestStore({target: url,
                                                  syncMode: true});
        store.fetch({
            scope: this,
            onComplete: function(response) {
                dojo.forEach(response, this.process_value, this);
            }
        });
    },
    process_value: function(character_value, index) {
        this.values.push(character_value.value_str);
    }   
});


// NumericRangeFilter
//
dojo.declare('NumericRangeFilter', [MultipleChoiceFilter], {
    process_value: function(character_value, index) {
        // We make this.values a one-element list: [{min: a, max: b}]
        if (this.values.Length) {
            var v = values[0];
            if (v.min > character_value.value_min)
                v.min = character_value.value_min;
            if (v.max < character_value.value_max)
                v.max = character_value.value_max;
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
    },
    load_default_filters: function() {
        var url = '/piles/';
        var store = new dojox.data.JsonRestStore({target: url, 
                                                  syncMode: true});
        var foo = store.fetchItemByIdentity({
            scope: this,
            identity: this.pile_slug,
            onItem: function(item) {
               for (var y = 0; y < item.default_filters.length; y++) {
                   var filter_json = item.default_filters[y];
                   this.add_filter(filter_json);
               }
            }
        });
    },
    add_filter: function(filter_json) {
        var filter_type;
        if (filter_json.value_type == 'LENGTH')
            filter_type = NumericRangeFilter;
        else
            filter_type = MultipleChoiceFilter;
        var filter = new filter_type(
            {
                friendly_name: filter_json.character_friendly_name,
                character_short_name: filter_json.character_short_name,
                order: filter_json.order,
                value_type: filter_json.value_type,
                pile_slug: this.pile_slug
            }
        );
        filter.load_values();

        // Add the filter to the manager's collection of default
        // filters.
        this.default_filters.push(filter);
    }
});

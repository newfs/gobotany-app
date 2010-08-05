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
    constructor: function(args) {
        console.log('Filter constructor called');
        console.log('args.friendly_name: ' + args.friendly_name);
        this.friendly_name = args.friendly_name;
        dojo.safeMixin(this, args);
    }
});

// MultipleChoiceFilter
//
dojo.declare("MultipleChoiceFilter", [Filter], {
    character_short_name: "", // Only one character field needed (unlike numeric?)
    constructor: function(args) {
        console.log('MultipleChoiceFilter constructor called');
        this.character_short_name = args.character_short_name;
    }
});

// TODO: NumericFilter?


// FilterManager
//
// A FilterManager object is responsible for pulling a pile's filters from 
// the REST API and maintaining a collection.
// It pulls a set of default filters, then later would pull more filters
// as needed.
//
dojo.declare("FilterManager", null, {
    pile_slug: "",
    default_filters: null,
    constructor: function(args) {
        console.log('FilterManager constructor called');
        this.pile_slug = args.pile_slug;
        this.default_filters = [ 'a', 'b', 'c' ]; // temp
    },
    load_default_filters: function() {
        console.log('inside load_default_filters: pile_slug=' + 
                    this.pile_slug);
        var url = '/piles/';
        var store = new dojox.data.JsonRestStore({target: url});
        store.fetchItemByIdentity({
            identity: this.pile_slug,
            onItem: function(item) {
               for (var y = 0; y < item.default_filters.length; y++) {
                    var filter_json = item.default_filters[y];
                    var filter = new MultipleChoiceFilter({
                        friendly_name: filter_json.character_friendly_name,
                        character_short_name: filter_json.character_short_name,
                        order: filter_json.order });
                    console.log(filter.friendly_name + ' ' + 
                                filter.character_short_name + ' ' + 
                                filter.order);
                    // TODO: add the filter to the manager's collection of
                    // default filters.
                    //this.default_filters.push('foo'); //filter); // undefined - scope ?
                    console.log('can we see the pile slug? ' + this.pile_slug);
                }
            }
        });
    }
});

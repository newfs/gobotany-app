// Non-UI filter code, for use in multiple applications.

// Global declaration for JSLint (http://www.jslint.com/)
/*global console, dojo, dojox, gobotany */

dojo.provide('gobotany.filters');
dojo.require('dojox.data.JsonRestStore');

dojo.declare('gobotany.filters.Filter', null, {
    character_short_name: '',
    friendly_name: '',
    order: 0,
    pile_slug: '',
    value_type: '',
    unit: '',
    key_characteristics: null,
    notable_exceptions: null,
    selected_value: null,
    filter_callback: null,

    constructor: function(args) {
        this.character_short_name = args.character_short_name;
        this.friendly_name = args.friendly_name;
        this.order = args.order;
        this.pile_slug = args.pile_slug;
        this.value_type = args.value_type;
        this.unit = args.unit;
        this.filter_callback = args.filter_callback;
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
dojo.declare('gobotany.filters.MultipleChoiceFilter', 
             [gobotany.filters.Filter], {
    values: null, // List of character value objects from the JSON
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
        // We make this.values an object: {min: a, max: b}
        if (this.values.length == 0) this.values = {};
        if (character_value.value == null) return;
        var v = this.values;
        var vmin = character_value.value[0];
        var vmax = character_value.value[1];
        if (vmin != null && (v.min == null || v.min > vmin)) v.min = vmin;
        if (vmax != null && (v.max == null || v.max < vmax)) v.max = vmax;
    }
});


// FilterManager
//
// A FilterManager object is responsible for pulling a pile's filters from
// the REST API and maintaining a collection.
// It pulls a set of default filters, then later would pull more filters
// as needed.
//
dojo.declare('gobotany.filters.FilterManager', null, {
    pile_slug: '',
    filters: null,
    species_count: 0,
    species_ids: [],
    entries: [],
    constructor: function(args) {
        this.pile_slug = args.pile_slug;
        this.plant_preview_characters = [];
        this.filters = [];
        this.filters_loading = 0;

        if (!args.pile_url) args.pile_url = '/piles/';
        if (!args.taxon_url) args.taxon_url = '/taxon/';

        this.chars_store = new dojox.data.JsonRestStore({target: args.pile_url + args.pile_slug + '/characters/'});
        this.result_store = new dojox.data.JsonRestStore({target: args.taxon_url, 
                                                          idAttribute: 'scientific_name'});
    },

    query_best_filters: function(args) {
        var choose_best = 3;
        if (args.choose_best)
            choose_best = args.choose_best;
        this.chars_store.fetch({
            query: {choose_best: choose_best,
                    species_id: this.species_ids || [],
                    character_group_id: args.character_group_ids || [],
                    exclude: args.existing_characters || []},
            scope: {filter_manager: this, args: args},
            onComplete: args.onLoaded,
        });
    },
    query_filters: function(args) {
        this.chars_store.fetch({
            query: {include: args.short_names || []},
            scope: {filter_manager: this, args: args},
            onComplete: args.onLoaded,
        });
    },
    on_pile_info_loaded: function() {},
    on_default_filters_loaded: function() {},

    get_filter: function(short_name) {
        for (var x = 0; x < this.filters.length; x++) {
            if (this.filters[x].character_short_name === short_name) {
                return this.filters[x];
            }
        }
        return false;
    },
    has_filter: function(short_name) {
        for (var x = 0; x < this.filters.length; x++)
            if (this.filters[x].character_short_name === short_name)
                return true;
        return false;
    },
    remove_filter: function(short_name) {
        for (var x = 0; x < this.filters.length; x++) {
            if (this.filters[x].character_short_name === short_name) {
                var filter = this.filters[x];
                this.filters.splice(x, 1);
                this.on_filter_removed(filter);
                return;
            }
        }
    },
    add_filter: function(obj) {
        // summary:
        //     Add a filter to this manager
        // description:
        //     Add the given object as a filter to this manager.  This
        //     function does no value loading or other side effects.
        // obj:
        //     Either a gobotany.filters.Filter instance or a kwArgs object.
        //     The kwArgs object should be something that can be passed
        //     into gobotany.filters.filter_factory().

        var f = obj;
        if (!obj.isInstanceOf || !obj.isInstanceOf(gobotany.filters.Filter))
            f = gobotany.filters.filter_factory(obj);
        this.filters.push(f);
        return f;
    },
    add_callback_filter: function(args) {
        // summary:
        //     Add a callback filter to this manager
        // description:
        //     Add the given object as a callback filter to this
        //     manager.  A callback filter is a filter with
        //     a callback function that will be used realtime
        //     to filter items.
        // args:
        //     a kwArgs object suitable for passing into
        //     'new gobotany.filters.Filter()'

        var filter_args = gobotany.utils.clone(args);
        filter_args.pile_slug = this.pile_slug;
        var filter = new gobotany.filters.Filter(filter_args);
        this.filters.push(filter);
        console.log('add_callback_filter: ' + filter.character_short_name);
    },
    set_selected_value: function(character_short_name, selected_value) {
        for (var i = 0; i < this.filters.length; i++) {
            if (this.filters[i].character_short_name ===
                  character_short_name) {
                // Character values must be stringified, since their
                // .length is checked before allowing them to become
                // part of our query URL.
                if (selected_value != null)
                    selected_value = String(selected_value);
                this.filters[i].selected_value = selected_value;
                this.on_filter_changed(this.filters[i], selected_value);
                return;
            }
        }
        console.log('FilterManager cannot set a value for unknown filter',
                    character_short_name)
    },
    get_selected_value: function(character_short_name) {
        var selected_value = null;
        for (var i = 0; i < this.filters.length; i++) {
            if (this.filters[i].character_short_name === character_short_name)
                return this.filters[i].selected_value;
        }
        return undefined;
    },
    set_count_for_value: function(character_short_name, value_name, count) {
        for (var i = 0; i < this.filters.length; i++) {
            var filter = this.filters[i];
            if (filter.character_short_name === character_short_name) {
                // Found the filter; now look for the character value.
                for (var j = 0; j < filter.values.length; j++) {
                    if (filter.values[j].value === value_name) {
                        filter.values[j].count = count;
                        return;
                    }
                }
                return;
            }
        }
        console.log('FilterManager cannot set a count for unknown filter: ',
                    character_short_name);
    },
    on_filter_added: function(filter) {},
    on_filter_removed: function(filter) {},
    on_filter_changed: function(filter) {},

    as_query_string: function() {
        var filter_names = [];
        var obj = {};
        for (var x = 0; x < this.filters.length; x++) {
            var f = this.filters[x];
            filter_names.push(f.character_short_name);
            obj[f.character_short_name] = f.selected_value;
        }

        return '_filters=' + filter_names.join(',') + '&' + dojo.objectToQuery(obj);
    },

    empty_filters: function() {
        this.filters = [];
    },
    perform_query: function(args) {
        var content = {pile: this.pile_slug};
        var special = [];
        console.log('FilterManager: running filtered query');
        for (var i = 0; i < this.filters.length; i++) {
            var filter = this.filters[i];

            if (filter.filter_callback != null) {
                special.push(filter);
            }

            if (filter.selected_value !== null && 
                filter.selected_value !== undefined &&
                filter.selected_value.length) {

                content[filter.character_short_name] = filter.selected_value;
            }
        }

        // Add the filter names for which to return character value counts.
        var filter_short_names = args['filter_short_names'];
        if (filter_short_names.length) {
            short_names = '';
            for (var i = 0; i < filter_short_names.length; i++) {
                if (i > 0) {
                    short_names += ',';
                }
                short_names += filter_short_names[i];
            }
            content['_counts_for'] = short_names;
        }

        this.result_store.fetch({
            scope: this,
            query: content,
            onComplete: function(data) {
                this.species_count = data.items.length;
                this.species_ids = [];
                for (i=0; i < data.items.length; i++)
                    this.species_ids[i] = data.items[i].id;

                if (special.length > 0) {
                    // run special filters
                    var newdata = [];
                    for (var x = 0; x < data.items.length; x++) { 
                        var item = data.items[x];
                        var removed = false;
                        for (var y = 0; y < special.length; y++) {
                            var callback = special[y].filter_callback;
                            if (!callback(special[y], item)) {
                                removed = true;
                                break;
                            }
                        }

                        if (!removed)
                            newdata.push(item);
                    }
                    data.items = newdata;
                    console.log('FilterManager.run_filtered_query: data was specially filtered');
                }
                
                // Process counts for filter character values.
                for (i = 0; i < data.value_counts.length; i++) {
                    var filter = data.value_counts[i];
                    var counts = filter['counts'];
                    for (var value_name in counts) {
                        if (counts.hasOwnProperty(value_name) &&
                            value_name !== '__parent') {

                            this.set_count_for_value(filter['name'],
                                value_name, counts[value_name]);
                        }
                    }
                }

                // Call the passed-in callback function.
                if (args && args.on_complete)
                    args.on_complete(data);
                this.on_new_results(data);
            },
            onError: function(error) {
                console.log('Taxon search encountered an error!');
                console.log(error);
                if (args && args.on_error)
                    args.on_error(error);
            }
        });
    },

    on_new_results: function(data) {}
});


dojo.declare('gobotany.filters.FilterLoadingWatcher', null, {
    constructor: function(filters) {
        this.filters = filters;
        this._filters_loading = 0;
    },

    load_values: function(args) {
        this._filters_loading = this.filters.length;
        var loading_args = {};
        if (args.on_values_loaded) {
            loading_args.onLoaded = dojo.hitch(this, function() {
                this._filters_loading--;
                if (this._filters_loading == 0)
                    args.on_values_loaded(this.filters);
            });
        }
            
        for (var y = 0; y < this.filters.length; y++) {
            var filter = this.filters[y];
            filter.load_values(loading_args);
        }
    }
    
});

gobotany.filters.filter_factory = function(args) {
    var filter_type;

    if (args.value_type == 'LENGTH') {
        filter_type = gobotany.filters.NumericRangeFilter;
    } else if (args.value_type == 'TEXT')  {
        filter_type = gobotany.filters.MultipleChoiceFilter;
    } else {
        filter_type = gobotany.filters.Filter;
    }

    var notable_exceptions = args.notable_exceptions;
    var key_characteristics = args.key_characteristics;
    if (args.filter) {
        notable_exceptions = args.filter.notable_exceptions;
        key_characteristics = args.filter.key_characteristics;
    }

    var filter = new filter_type({
        friendly_name: args.character_friendly_name || args.friendly_name,
        character_short_name: args.character_short_name || args.short_name,
        order: args.order,
        notable_exceptions: notable_exceptions,
        key_characteristics: key_characteristics,
        value_type: args.value_type,
        unit: args.unit,
        pile_slug: args.pile_slug
    });

    return filter;
};

// Non-UI filter code, for use in multiple applications.

// Global declaration for JSLint (http://www.jslint.com/)
/*global console, dojo, dojox, gobotany */

dojo.provide('gobotany.filters');
dojo.require('dojox.data.JsonRestStore');

var get_json = function(path, _this, load) {
    var u = API_URL + path;
    if (path.substr(-1) !== '/') u += '/';
    dojo.xhrGet({url: u, handleAs: 'json', load: dojo.hitch(_this, load)});
};

var intersect = function(a, b) {
    var ai = 0, bi = 0;
    var result = new Array();
    while (ai < a.length && bi < b.length) {
        if (a[ai] < b[bi]) ai++;
        else if (a[ai] > b[bi]) bi++;
        else { result.push(a[ai]); ai++; bi++; }
    }
    return result;
};

dojo.declare('gobotany.filters.Filter', null, {
    character_short_name: '',
    friendly_name: '',
    order: 0,
    pile_slug: '',
    value_type: '',
    unit: '',
    key_characteristics: null,
    notable_exceptions: null,
    question: null,
    hint: null,
    selected_value: null,
    filter_callback: null,
    vectors: false,  // array of vectors
    vectormap: false,  // character short_name -> vector

    constructor: function(args) {
        this.character_short_name = args.character_short_name;
        this.friendly_name = args.friendly_name;
        this.order = args.order;
        this.pile_slug = args.pile_slug;
        this.value_type = args.value_type;
        this.unit = args.unit;
        this.filter_callback = args.filter_callback;
        dojo.safeMixin(this, args);
        var url = API_URL + 'piles/' + this.pile_slug + '/' +
                  this.character_short_name + '/';
        this.store = new dojox.data.JsonRestStore({target: url});
    },
    load_values: function(args) {
        if (args && args.onLoaded) {
            args.onLoaded();
        }
    },
    // load_vectors({onload: function})
    // Does an async load of the filter's species id list, then invokes
    // the caller-supplied callback.  The vector is stored, so the second
    // and subsequent invocations can invoke the callback immediately.
    load_vectors: function(args) {
        var path = 'vectors/character/' + this.character_short_name;
        if (this.vectors === false) {
            get_json(path, this, function(data) {
                this.vectors = data;
                this.vectormap = {};
                for (var i = 0; i < this.vectors.length; i++) {
                    var v = this.vectors[i];
                    this.vectormap[v.value] = v.species;
                }
                console.log('vectors loaded for', this.character_short_name);
                args.onload(this);
            });
        } else
            args.onload(this);
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
    },
    get_value_object: function(value_string) {
        var i = 0;
        for (i = 0; i < this.values.length; i++) {
            if (this.values[i].value === value_string) {
                return this.values[i];
            }
        }
        return undefined;
    }
});


// NumericRangeFilter
//
dojo.declare('gobotany.filters.NumericRangeFilter',
             [gobotany.filters.MultipleChoiceFilter], {
    process_value: function(character_value, index) {
        // We make this.values an object: {min: a, max: b}
        if (this.values.length === 0) {
            this.values = {};
        }
        if (character_value.value === null) {
            return;
        }
        var v = this.values;
        var vmin = character_value.value[0];
        var vmax = character_value.value[1];
        if (vmin !== undefined && (v.min === undefined || v.min > vmin)) {
            v.min = vmin;
        }
        if (vmax !== undefined && (v.max === undefined || v.max < vmax)) {
            v.max = vmax;
        }
    },
    is_length: function() {
        // Return true if this numeric filter appears to measure a length
        // rather than a count.
        return ((this.character_short_name.indexOf('length') > -1) ||
                (this.character_short_name.indexOf('width') > -1) ||
                (this.character_short_name.indexOf('height') > -1) ||
                (this.character_short_name.indexOf('thickness') > -1));
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
    all_species: {},  // species_id -> { species object }
    species_count: 0,
    species_ids: [],
    entries: [],
    fetch_counter: 0,  // to assure that most recent request "wins"

    constructor: function(args) {
        this.pile_slug = args.pile_slug;
        this.plant_preview_characters = [];
        this.filters = [];
        this.base_vector = false;  // intersection(simple_vector, pile_vector)

        if (!args.pile_url) {
            args.pile_url = API_URL + 'piles/';
        }
        if (!args.taxon_url) {
            args.taxon_url = API_URL + 'taxon/';
        }

        this.chars_store = new dojox.data.JsonRestStore(
            {target: args.pile_url + args.pile_slug + '/characters/'});
        this.result_store = new dojox.data.JsonRestStore(
            {target: args.taxon_url, idAttribute: 'scientific_name'});

        this.stage1();
    },

    // When a FilterManager is first created, it preloads the list of
    // species applicable to its key and pile and then fetches the data
    // for those species.  This is performed in stages.

    stage1: function() {
        this.stage1_countdown = 3;
        get_json('species/' + this.pile_slug, this, function(data) {
            for (var i = 0; i < data.length; i++) {
                var info = data[i];
                this.all_species[info.id] = info;
            }
            this.stage2();
        });
        get_json('vectors/key/simple', this, function(data) {
            this.simple_vector = data[0].species;
            this.stage2();
        });
        get_json('vectors/pile/' + this.pile_slug, this, function(data) {
            this.pile_vector = data[0].species;
            this.stage2();
        });
    },
    stage2: function() {
        this.stage1_countdown--;
        if (this.stage1_countdown)
            return;
        this.base_vector = intersect(this.simple_vector, this.pile_vector);
        console.log('base_vector:', this.base_vector.length, 'species');
    },

    // // Callback invoked each time a vector is returned.
    // filter_loaded: function() {
    //     this.filters_loading = this.filters_loading - 1;
    //     if (this.filters_loading > 0)
    //         return;  // do nothing until all outstanding filters load
    //     if (this.base_vector === false) {
    //     }
    // },

    // Given a filter, returns an object whose attributes are character
    // value short names and whose values are the number of species that
    // would remain if the results were filtered by that value.
    compute_filter_counts: function(filter) {
        console.log('compute_filter_counts()');
        var vector = this.base_vector;

        // TODO: there might be a race condition here until the
        // architecure is sufficiently reworked to assure that each
        // active value's vector has been loaded by the time we get here.
        for (var i = 0; i < this.filters.length; i++) {
            var f = this.filters[i];
            if (f === filter)
                continue; // ignore this filter itself
            if (f.selected_value) {
                var species = f.vectormap[f.selected_value];
                vector = intersect(vector, species);
            }
        }
        var counts = {};
        for (var i = 0; i < filter.vectors.length; i++) {
            var v = filter.vectors[i];
            counts[v.value] = intersect(vector, v.species).length;
        }
        return counts;
    },

    query_best_filters: function(args) {
        var choose_best = 3;
        if (args.choose_best) {
            choose_best = args.choose_best;
        }
        this.chars_store.fetch({
            query: {choose_best: choose_best,
                    species_id: this.species_ids || [],
                    character_group_id: args.character_group_ids || [],
                    exclude: args.existing_characters || []},
            scope: {filter_manager: this, args: args},
            onComplete: args.onLoaded
        });
    },
    query_filters: function(args) {
        this.chars_store.fetch({
            query: {include: args.short_names || []},
            scope: {filter_manager: this, args: args},
            onComplete: args.onLoaded
        });
    },
    on_pile_info_loaded: function() {},
    on_default_filters_loaded: function() {},

    get_filter: function(short_name) {
        var x = 0;
        for (x = 0; x < this.filters.length; x++) {
            if (this.filters[x].character_short_name === short_name) {
                return this.filters[x];
            }
        }
        return false;
    },
    has_filter: function(short_name) {
        var x = 0;
        for (x = 0; x < this.filters.length; x++) {
            if (this.filters[x].character_short_name === short_name) {
                return true;
            }
        }
        return false;
    },
    remove_filter: function(short_name) {
        var x = 0;
        for (x = 0; x < this.filters.length; x++) {
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
        if (!obj.isInstanceOf ||
            !obj.isInstanceOf(gobotany.filters.Filter)) {

            f = gobotany.filters.filter_factory(obj);
        }
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
        console.log('SET', character_short_name, selected_value);
        var i = 0;
        for (i = 0; i < this.filters.length; i++) {
            if (this.filters[i].character_short_name ===
                  character_short_name) {
                // Character values must be stringified, since their
                // .length is checked before allowing them to become
                // part of our query URL.
                if (selected_value !== undefined) {
                    selected_value = String(selected_value);
                }
                this.filters[i].selected_value = selected_value;
                if (character_short_name == 'family' ||
                    character_short_name == 'genus')
                    return;
                this.filters[i].load_vectors({
                    onload: dojo.hitch(this, function() {
                        this.on_filter_changed(this.filters[i], selected_value);
                    })});
                return;
            }
        }
        console.log('FilterManager cannot set a value for unknown filter',
                    character_short_name);
    },
    get_selected_value: function(character_short_name) {
        var i = 0;
        for (i = 0; i < this.filters.length; i++) {
            if (this.filters[i].character_short_name ===
                character_short_name) {
                return this.filters[i].selected_value;
            }
        }
        return undefined;
    },
    on_filter_added: function(filter) {},
    on_filter_removed: function(filter) {},
    on_filter_changed: function(filter) {},

    as_query_string: function() {
        var filter_names = [];
        var obj = {};
        var x = 0;
        for (x = 0; x < this.filters.length; x++) {
            var f = this.filters[x];
            filter_names.push(f.character_short_name);
            obj[f.character_short_name] = f.selected_value;
        }

        return '_filters=' + filter_names.join(',') + '&' +
            dojo.objectToQuery(obj);
    },

    empty_filters: function() {
        this.filters = [];
    },
    perform_query: function(args) {
        console.log('FilterManager: running filtered query');

        // Narrow down the pile's list of species to only those that
        // match the selected filters.

        var vector = this.base_vector;

        for (var i = 0; i < this.filters.length; i++) {
            var filter = this.filters[i];
            if (filter.selected_value !== null &&
                filter.selected_value !== undefined &&
                filter.selected_value.length) {
                var fvector = filter.vectormap[filter.selected_value];
                vector = intersect(vector, fvector);
            }
        }

        // Update our state with this final result.

        this.species_ids = vector;
        this.species_count = vector.length;

        // Call the passed-in callback function.
        var species_list = [];
        for (var i = 0; i < vector.length; i++)
            species_list.push(this.all_species[vector[i]]);

        var data = {items: species_list};
        if (args && args.on_complete)
            args.on_complete(data);
        this.on_new_results(data);
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
                if (this._filters_loading === 0) {
                    args.on_values_loaded(this.filters);
                }
            });
        }
        var y = 0;
        for (y = 0; y < this.filters.length; y++) {
            var filter = this.filters[y];
            filter.load_values(loading_args);
        }
    }
});

gobotany.filters.filter_factory = function(args) {
    var filter_type;

    if (args.value_type === 'LENGTH') {
        filter_type = gobotany.filters.NumericRangeFilter;
    }
    else if (args.value_type === 'TEXT') {
        filter_type = gobotany.filters.MultipleChoiceFilter;
    }
    else {
        filter_type = gobotany.filters.Filter;
    }

    var notable_exceptions = args.notable_exceptions;
    var key_characteristics = args.key_characteristics;
    var question = args.question;
    var hint = args.hint;
    if (args.filter) {
        notable_exceptions = args.filter.notable_exceptions;
        key_characteristics = args.filter.key_characteristics;
        question = args.filter.question;
        hint = args.filter.hint;
    }

    var filter = new filter_type({
        friendly_name: args.character_friendly_name || args.friendly_name,
        character_short_name: args.character_short_name || args.short_name,
        order: args.order,
        notable_exceptions: notable_exceptions,
        key_characteristics: key_characteristics,
        question: question,
        hint: hint,
        value_type: args.value_type,
        unit: args.unit,
        pile_slug: args.pile_slug
    });

    return filter;
};

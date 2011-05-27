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

var intsort = function(array) {
    array.sort(function(a, b) {return a - b});
};

/**
 * Compute the intersection of two already-sorted lists of species ids.
 *
 * @param {Array} a One list of integer species ids.
 * @param {Array} b Another list of integer species ids.
 * @return {Array} The resulting list of integer species ids.
 */
gobotany.filters.intersect = function(a, b) {
    var ai = 0, bi = 0;
    var result = new Array();
    while (ai < a.length && bi < b.length) {
        if (a[ai] < b[bi]) ai++;
        else if (a[ai] > b[bi]) bi++;
        else { result.push(a[ai]); ai++; bi++; }
    }
    return result;
};

var intersect = gobotany.filters.intersect;

dojo.declare('gobotany.filters.Filter', null, {
    selected_value: null,
    values: false,  // load_values() creates [value, ...] array
    choicemap: false,  // load_values() creates {short_name: value, ...}
    min: null,
    max: null,

    constructor: function(args, args2) {
        this.manager = args2.manager;  // FilterManager to which this belongs

        this.order = args.order;
        this.pile_slug = args.pile_slug;
        this.unit = args.unit;
        this.value_type = args.value_type;

        this.character_short_name =
            args.character_short_name || args.short_name;
        this.friendly_name =
            args.character_friendly_name || args.friendly_name;

        var f = args.filter ? args.filter : args;

        this.hint = f.hint;
        this.key_characteristics = f.key_characteristics;
        this.notable_exceptions = f.notable_exceptions;
        this.question = f.question;

        dojo.safeMixin(this, args);
    },
    // load_values({base_vector: [...], onload: function})
    // Does an async load of the filter's species id list, then invokes
    // the caller-supplied callback.  The vector is stored so the second
    // and subsequent invocations can invoke the callback immediately.
    // Values that have no species in common with the given base_vector
    // are not stored, since they do not apply to this key and pile.
    load_values: function(args) {
        var url = 'vectors/character/' + this.character_short_name;

        if (this.values !== false) {
            if (args.onload !== undefined) args.onload(this);
            return;
        }

        get_json(url, this, function(data) {
            this.values = [];
            this.choicemap = {};
            if (!args.base_vector) {
                console.log('load_values: species apparently not ' +
                            'loaded yet (base vector is false)');
            }
            for (var i = 0; i < data.length; i++) {
                var value = data[i];
                this.values.push(value);

                if (value.choice !== null)
                    this.choicemap[value.choice] = value;

                if (value.min !== null)
                    if (this.min === null || value.min < this.min)
                        this.min = value.min;

                if (value.max !== null)
                    if (this.max === null || value.max > this.max)
                        this.max = value.max;
            }
            console.log(this.values.length + ' values loaded for',
                        this.character_short_name);

            // If our FilterManager has already finished loading and
            // computing its base_vector, then we should cull ourselves.
            if (this.manager.base_vector !== null)
                this.cull_values();

            if (args.onload !== undefined) args.onload(this);
        });
    },
    // Remove values that have absolutely no species in common with our
    // FilterManager's base_vector, so that pile-irrelevant character
    // values do not get displayed when a filter is pulled up.
    cull_values: function() {
        var base_vector = this.manager.base_vector;
        for (var i = this.values.length - 1; i >= 0; i--)
            if (intersect(base_vector, this.values[i].species).length === 0)
                this.values.splice(i, 1);
    },
    // Return true if the name of this filter appears to name a length
    // value (as opposed to something like a count).
    is_length: function() {
        return ((this.character_short_name.indexOf('length') > -1) ||
                (this.character_short_name.indexOf('width') > -1) ||
                (this.character_short_name.indexOf('height') > -1) ||
                (this.character_short_name.indexOf('thickness') > -1));
    },
    // For a numeric filter, figure out which ranges of values are legal
    // given a possible set of species as a species ID array.  Returns a
    // sorted list of disjoint ranges like:
    // [{min: 2, max: 5}, {min: 7, max: 9}]
    allowed_ranges: function(vector) {
        var ranges = [];
        for (i = 0; i < this.values.length; i++) {
            var value = this.values[i];
            var vmin = value.min;
            var vmax = value.max;

            if (vmin === null || vmax === null)
                continue;  // ignore values that are not ranges anyway

            if (intersect(vector, value.species).length == 0)
                continue;  // ignore values that apply to none of these species

            // First we skip any ranges lying entirely to the left of this one.

            var j = 0;
            for (j = 0; j < ranges.length && ranges[j].max < value.min; j++);

            // Next, we absorb every range with which we overlap.

            while (j < ranges.length &&
                   vmin <= ranges[j].max && ranges[j].min <= vmax) {
                vmin = Math.min(ranges[j].min, vmin);
                vmax = Math.max(ranges[j].max, vmax);
                ranges.splice(j, 1);
            }

            // Finally, we insert this new range into the list.

            ranges.splice(j, 0, {min: vmin, max: vmax});
        }
        return ranges;
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
    fetch_counter: 0,  // to assure that most recent request "wins"

    constructor: function(args) {
        this.entries = [];
        this.filters = [];
        this.base_vector = null;  // intersection(simple_vector, pile_vector)
        this.pile_slug = args.pile_slug;
        this.plant_preview_characters = [];
        this.species_by_id = {};  // species_id -> species_obj
        this.species_by_scientific_name = {}; // scientific_name -> species_obj
        this.species_ids = [];
        this.onload = args.onload;

        if (!args.pile_url) {
            args.pile_url = API_URL + 'piles/';
        }

        this.chars_store = new dojox.data.JsonRestStore(
            {target: args.pile_url + args.pile_slug + '/characters/'});

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
                this.species_by_id[info.id] = info;
                this.species_by_scientific_name[info.scientific_name] = info;
            }
            this.build_family_genus_filters(data);
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

        // Since this.base_vector has been null until this moment, none
        // of the filters loaded so far has been able to cull itself of
        // inapplicable values.
        for (var i = 0; i < this.filters.length; i++)
            this.filters[i].cull_values();

        var onload = this.onload;
        if (onload !== undefined) onload(this);
    },

    // build_family_genus_filters()
    // Generate synthetic family and genus filters, whose vectors are
    // computed from the attributes "family" and "genus" of our own
    // species list, instead of being pulled from a separate API call.

    build_family_genus_filters: function(species_list) {
        var m = {manager: this};
        var f = gobotany.filters.Filter({character_short_name: 'family'}, m);
        var g = gobotany.filters.Filter({character_short_name: 'genus'}, m);
        f.choicemap = {};
        g.choicemap = {};
        for (var i = 0; i < species_list.length; i++) {
            var family = species_list[i].family;
            if (!f.choicemap[family])
                f.choicemap[family] = {species: []};
            f.choicemap[family].species.push(species_list[i].id);
            var genus = species_list[i].genus;
            if (!g.choicemap[genus])
                g.choicemap[genus] = {species: []};
            g.choicemap[genus].species.push(species_list[i].id);
        }
        for (var family in f.choicemap)
            intsort(f.choicemap[family].species);
        for (var genus in g.choicemap)
            intsort(g.choicemap[genus].species);
        this.filters.push(f);
        this.filters.push(g);
    },

    // get_species({scientific_name: s, onload: function})
    // Return the information about a particular species.

    get_species: function(args) {
        args.onload(this.species_by_scientific_name[args.scientific_name]);
    },

    // Figure out which species would be selected if the filter with the
    // given short_name did not have a currently selected value.
    compute_species_without: function(short_name) {
        var selected_value = this.get_selected_value(short_name);
        if (selected_value) {
            this.set_selected_value(short_name, null);
            var vector = this.compute_query();
            this.set_selected_value(short_name, selected_value);
        } else {
            var vector = this.species_ids;
        }
        return vector;
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
        //     into gobotany.filters.Filter's constructor.

        var f = obj;
        if (!obj.isInstanceOf || !obj.isInstanceOf(gobotany.filters.Filter)) {
            f = new gobotany.filters.Filter(obj, {manager: this});
        }
        this.filters.push(f);
        return f;
    },
    // Always call set_selected_value() with a selected_value of null, a
    // string, or a number.
    set_selected_value: function(character_short_name, selected_value) {
        console.log('SET', character_short_name, selected_value);
        if (selected_value === undefined || selected_value === '')
            selected_value = null;

        for (i = 0; i < this.filters.length; i++) {
            var filter = this.filters[i];
            if (filter.character_short_name === character_short_name) {
                // Character values must be stringified, since their
                // .length is checked before allowing them to become
                // part of our query URL.
                if (selected_value !== null) {
                    selected_value = String(selected_value);
                }
                // Ignore multiple choice values which are not valid.
                if (selected_value !== null &&
                    filter.value_type == 'TEXT' &&
                    filter.choicemap[selected_value] === undefined) {
                    console.log('Error: the filter', filter.short_name,
                                'cannot take the value', selected_value);
                    return;
                }
                // Set the value.
                this.filters[i].selected_value = selected_value;
                if (character_short_name == 'family' ||
                    character_short_name == 'genus')
                    return;
                this.filters[i].load_values({base_vector: this.base_vector});
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

    // Return the list of species ids that remain selected after
    // applying all currently active filters; this method does NOT save
    // the results or alter the state of this FilterManager.
    compute_query: function() {
        var vector = this.base_vector;

        for (var i = 0; i < this.filters.length; i++) {
            var filter = this.filters[i];
            var sv = filter.selected_value;
            if (sv !== null) {
                if (isNaN(sv) && sv.length) {
                    // looking up a multiple-choice filter is a single step
                    var value = filter.choicemap[sv];
                    vector = intersect(vector, value.species);
                } else if (!isNaN(sv)) {
                    // a number has to be checked against each species' range
                    var fvector = [];
                    for (j = 0; j < filter.values.length; j++) {
                        var value = filter.values[j];
                        if (sv >= value.min && sv <= value.max)
                            fvector = fvector.concat(value.species);
                    }
                    fvector.sort();
                    vector = intersect(vector, fvector);
                }
            }
        }

        return vector;
    },

    // Apply all active filters, and update all of our FilterManager
    // attributes to reflect the result.
    perform_query: function(args) {
        console.log('FilterManager: running filtered query');
        vector = this.compute_query();

        // Update our state with this final result.

        this.species_ids = vector;
        this.species_count = vector.length;

        var species_list = [];
        for (var i = 0; i < vector.length; i++)
            species_list.push(this.species_by_id[vector[i]]);

        // Sort and return the matching species.

        species_list.sort(function(a, b) {
            return a.scientific_name < b.scientific_name ? -1 : 1;
        });

        var data = {items: species_list};
        if (args && args.on_complete)
            args.on_complete(data);
    }
});

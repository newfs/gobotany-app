// Non-UI filter code, for use in multiple applications.

// Global declaration for JSLint (http://www.jslint.com/)
/*global console, dojo, dojox, gobotany */

/*
   Dojo topics:

   FilterManager subscribes to '/sk/filter/change': re-runs its query
      logic to compute the set of species that match the new filter
      values.  When the new list has been computed, publishes
      '/filters/query-result' with the new species list as the
      associated value.
 */

dojo.provide('gobotany.filters');

dojo.declare('gobotany.filters.Filter', null, {
    selected_value: null,
    values: false,  // load_values() creates [value, ...] array
    choicemap: false,  // load_values() creates {short_name: value, ...}
    min: null,
    max: null,

    constructor: function(args) {
        this.finished_loading = $.Deferred();

        this.pile_slug = args.pile_slug;
        this.value_type = args.value_type;
        this.character_short_name = this.short_name = args.short_name;
        this.friendly_name = args.friendly_name;
        this.hint = args.hint;
        this.question = args.question;
    },
    // load_values()
    // Kicks off a fetch of the filter's vectors (if a fetch has not been
    // started already), and returns a Deferred supplying their values.
    load_values: function() {

        if (this.values !== false)
            return this.finished_loading;

        $.when(
            simplekey_resources.base_vector({
                key_name: 'simple', pile_slug: this.pile_slug
            }),
            simplekey_resources.character_vector(this.short_name)
        ).done(_.bind(this.install_values, this));
        return this.finished_loading;
    },

    /* Install the given array of values as the choices offered by this
       filter. */
    install_values: function(base_vector, values) {
        this.values = [];
        this.choicemap = {};

        var knowns = [];  // species with any value whatsoever, even NA
        for (var i = 0; i < values.length; i++) {
            var value = values[i];
            value.taxa = _.intersect(value.taxa, base_vector);
            if (!value.taxa)
                continue;  // value does not apply to this pile

            var knowns = _.uniq(knowns.concat(value.taxa));
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

        // Report on whether every species in this pile has a value
        // for this filter, or whether some are unknown.
        this.unknowns = _.without.apply(0, [base_vector].concat(knowns));
        console.log(this.character_short_name, '- covers', knowns.length,
                    '/', base_vector.length, 'taxa');

        this.finished_loading.resolve(this);
    },

    // Return true if the name of this filter appears to name a length
    // value (as opposed to something like a count).
    is_length: function() {
        return ((this.character_short_name.indexOf('length') > -1) ||
                (this.character_short_name.indexOf('width') > -1) ||
                (this.character_short_name.indexOf('height') > -1) ||
                (this.character_short_name.indexOf('thickness') > -1));
    },
    // Return the vector of species IDs for species that match a given
    // value for this character.
    species_matching: function(value) {
        if (this.value_type === 'TEXT') {
            // Looking up a multiple-choice filter is a single step.
            return this.choicemap[value].taxa;
        } else if (this.value_type === 'LENGTH') {
            // A number has to be checked against each species' range.
            var vector = [];
            if (value === null)
                return vector;
            for (var i = 0; i < this.values.length; i++) {
                var vi = this.values[i];
                if (vi.min === 0 && vi.max === 0)  // length way of saying "NA"
                    continue;
                if (value >= vi.min && value <= vi.max)
                    vector = vector.concat(vi.taxa);
            }
            vector.sort();
            return vector;
        } else
            console.log('Error: unknown value_type', this.value_type);
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

            if (vmin === 0 && vmax === 0)
                continue;  // ignore "NA" values

            if (_.intersect(vector, value.taxa).length == 0)
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

    constructor: function(args) {
        this.filters = [
            gobotany.filters.Filter({short_name: 'family', value_type: 'TEXT'}),
            gobotany.filters.Filter({short_name: 'genus', value_type: 'TEXT'})
        ];
        this.base_vector = null;
        this.pile_slug = args.pile_slug;
        this.species_by_id = {};  // species_id -> species_obj
        this.species_by_scientific_name = {}; // scientific_name -> species_obj
        this.species_ids = [];
        this.load_complete = $.Deferred();

        dojo.subscribe('/sk/filter/change', this, 'perform_query');

        this.start_loading();
    },

    // When a FilterManager is first created, it preloads the list of
    // species applicable to its key and pile and then fetches the data
    // for those species.  This is performed in stages.

    start_loading: function() {
        var taxa_sorted_out = $.Deferred();
        var fetch_pile_species = simplekey_resources.pile_species(
            this.pile_slug);
        var fetch_base_vector = simplekey_resources.base_vector({
            key_name: 'simple', pile_slug: this.pile_slug});

        fetch_pile_species.done(_.bind(function(species_list) {
            for (var i = 0; i < species_list.length; i++) {
                var info = species_list[i];
                this.species_by_id[info.id] = info;
                this.species_by_scientific_name[info.scientific_name] = info;
            }
            species_list.sort(function(a, b) {
                return a.scientific_name < b.scientific_name ? -1 : 1;
            });
            taxa_sorted_out.resolve(species_list);
        }, this));

        $.when(
            fetch_base_vector, taxa_sorted_out
        ).done(_.bind(function(base_vector, taxa_objects) {
            this.base_vector = base_vector;
            this.build_family_genus_filters(base_vector, taxa_objects);
            console.log('base_vector has', base_vector.length, 'species');
            this.load_complete.resolve();
        }, this));
    },

    // build_family_genus_filters()
    // Generate synthetic family and genus filters, whose vectors are
    // computed from the attributes "family" and "genus" of our own
    // species list, instead of being pulled from a separate API call.

    build_family_genus_filters: function(base_vector, taxa) {
        var families = _.chain(taxa).groupBy('family')
            .map(function(t, v) {return {choice: v, taxa: _.pluck(t, 'id')}})
            .value();
        this.get_filter('family').install_values(base_vector, families);

        var genera = _.chain(taxa).groupBy('genus')
            .map(function(t, v) {return {choice: v, taxa: _.pluck(t, 'id')}})
            .value();
        this.get_filter('genus').install_values(base_vector, genera);
    },

    get_taxon: function(scientific_name) {
        return this.species_by_scientific_name[scientific_name];
    },
    get_filter: function(short_name) {
        for (var i = 0; i < this.filters.length; i++)
            if (this.filters[i].short_name === short_name)
                return this.filters[i];
        console.log('Error: get_filter() unknown filter', short_name);
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
    add_filter: function(args) {
        var f = new gobotany.filters.Filter(args);
        this.filters.push(f);
        return f;
    },
    // Always call set_selected_value() with a selected_value of null, a
    // string, or a number.
    set_selected_value: function(short_name, selected_value) {
        console.log('SET', short_name, selected_value);

        if (selected_value === undefined || selected_value === '')
            selected_value = null;

        var filter = this.get_filter(short_name);

        // Character values must be stringified, since their .length is
        // checked before allowing them to become part of our query URL.
        if (selected_value !== null)
            selected_value = String(selected_value);

        // Ignore multiple choice values which are not valid.
        if (selected_value !== null &&
            filter.value_type == 'TEXT' &&
            filter.choicemap[selected_value] === undefined) {
            console.log('Error: the filter', filter.short_name,
                        'cannot take the value', selected_value);
            return;
        }
        // Set the value.
        filter.selected_value = selected_value;
        if (short_name == 'family' || short_name == 'genus')
            return;

        // In case this is the way we first find out about a filter,
        // make sure that its vectors are loaded.
        filter.load_values();
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

    // Return the list of taxon ids that remain after applying all of
    // the currently active filters.  If args is {'without': filter}
    // then that one filter is ignored in computing the result.
    compute_query: function(args) {
        var vector = this.base_vector;

        for (var i = 0; i < this.filters.length; i++) {
            var filter = this.filters[i];
            if (args && args.without === filter)
                continue;
            var sv = filter.selected_value;
            if (sv === null)
                continue;
            var matches = filter.species_matching(sv);
            var matches_and_unknowns = matches.concat(filter.unknowns);
            vector = _.intersect(vector, matches_and_unknowns);
        }

        return vector;
    },

    /* Given a filter, return a list of {taxa:, value:} objects showing
       which taxa would be left after filtering for each value. */
    compute_impact: function(filter) {
        var taxa = this.compute_query({without: filter});
        return _.map(filter.values, function(value) {
            return {taxa: _.intersect(taxa, value.taxa), value: value};
        });
    },

    // Apply all active filters, and update all of our FilterManager
    // attributes to reflect the result.
    perform_query: function() {
        console.log('FilterManager: running filtered query');

        var ids = this.species_ids = this.compute_query();
        var taxa_by_id = this.species_by_id;
        var taxa = _.map(ids, function(id) {return taxa_by_id[id]});
        taxa.sort(function(a, b) {
            return a.scientific_name < b.scientific_name ? -1 : 1;
        });
        dojo.publish('/filters/query-result', [{species_list: taxa}]);
    }
});

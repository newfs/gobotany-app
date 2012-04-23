define([
    'ember',
    'underscore-min'
], function() {return Ember.Object.extend({

    init: function() {
        var slug = this.slug;
        var is_length = (slug.indexOf('length') > -1) ||
            (slug.indexOf('width') > -1) ||
            (slug.indexOf('height') > -1) ||
            (slug.indexOf('thickness') > -1) ||
            (slug.indexOf('diameter') > -1);

        this.set('is_length', is_length);
        this.set('value', null);
        this.set('values', null);
        this.set('choicemap', {});
    },

    /* Install the list of values returned by the API for this filter. */

    install_values: function(args) {
        var values = _.filter(args.values, function(value) {
            // Throw out values that had no taxa in this pile.
            value.taxa = _.intersect(value.taxa, args.pile_taxa);
            return value.taxa.length;
        });
        var alltaxa = [];
        var choicemap = {};
        _.each(values, function(v) {
            alltaxa = _.union(alltaxa, v.taxa);
            if (v.choice)
                choicemap[v.choice] = v;
        });
        this.set('values', values);
        this.set('choicemap', choicemap);
        this.set('valueless_taxa', _.difference(args.pile_taxa, alltaxa));
    },

    /* Return the vector of taxa IDs for taxa that match a given value
       for this character. */

    taxa_matching: function(value) {
        if (arguments.length == 0)
            value = this.get('value');

        // Looking up a multiple-choice filter is a single step.
        if (this.value_type === 'TEXT') {
            return this.choicemap[value].taxa;

        // A number has to be checked against each range.
        } else if (this.value_type === 'LENGTH') {
            var values = _.filter(this.values, function(v) {
                var NA = (v.min == 0 && v.max == 0);
                return NA ? false : (value >= v.min && value <= v.max);
            });
            return _.uniq(_.flatten(_.pluck(values, 'taxa')));

        } else
            console.log('Error: unknown value_type', this.value_type);
    },

    /* For a numeric filter, figure out which ranges of values are still
     * legal given a list of taxa still on the page.  Returns a sorted
     * list of disjoint ranges like:
     * [{min: 2, max: 5}, {min: 7, max: 9}]
     */

    allowed_ranges: function(taxa) {
        var ranges = [];

        _.each(this.values, function(value) {
            var vmin = value.min;
            var vmax = value.max;

            if (vmin === null || vmax === null)
                return;  // ignore values that are not ranges anyway

            if (vmin === 0 && vmax === 0)
                return;  // ignore "NA" values

            if (_.intersect(taxa, value.taxa).length == 0)
                return;  // ignore values that apply to none of these species

            // First we skip any ranges lying entirely to the left of this one.

            var j;
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
        });
        return ranges;
    }

})});

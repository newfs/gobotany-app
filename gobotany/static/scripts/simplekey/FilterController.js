define([
    'bridge/ember',
    'bridge/jquery',
    'underscore-min',
    'simplekey/Filter'
], function(Ember, $, x, Filter) {return Ember.ArrayController.extend({

    init: function() {
        var taxadata = this.taxadata;
        delete this.taxadata;

        this.set('content', []);
        this.set('filtermap', {});
        this.set('pile_taxa', _.sortBy(_.pluck(taxadata, 'id'), this.numsort));
        this.build_classification_filter('family', taxadata);
        this.build_classification_filter('genus', taxadata);
        this.update();
    },

    build_classification_filter: function(name, taxadata) {
        var f = Filter.create({slug: name, value_type: 'TEXT'});
        var values = _.chain(taxadata).groupBy(name).map(function(taxad, v) {
            return {choice: v, taxa: _.pluck(taxad, 'id')};
        }).value();
        f.install_values({pile_taxa: this.pile_taxa, values: values});
        this.add(f);
    },

    add: function(filter) {
        this.addObject(filter);
        this.get('filtermap')[filter.slug] = filter;
    },

    // Run the query, but return rather than persist the results.

    compute: function(skip_filter) {
        var taxa = this.get('pile_taxa');
        this.forEach(function(f) {
            if (f !== skip_filter && f.value !== null && f.value != '') {
                var matches = f.taxa_matching().concat(f.valueless_taxa);
                taxa = _.intersect(taxa, matches);
            }
        });
        return _.sortBy(taxa, this.numsort);
    },

    // Run the query, saving the result so that observers get updates.

    update: function() {
        this.set('taxa', this.compute());
    }.observes('@each.value'),

    numsort: function(a, b) {return a - b}

})});

define([
    'ember',
    'jquery',
    'underscore-min',
    'simplekey/Filter'
], function(x, $, x, Filter) {return Ember.Object.extend({

    init: function(taxadata) {
        this.set('filters', []);
        this.set('filtermap', {});
        this.set('pile_taxa', _.sortBy(_.pluck(taxadata, 'id'), this.numsort));
        this.build_classification_filter('family', taxadata);
        this.build_classification_filter('genus', taxadata);
        this.update();
    },

    build_classification_filter: function(name, taxadata) {
        var f = new Filter({short_name: name, value_type: 'TEXT'});
        var values = _.chain(taxadata).groupBy(name).map(function(taxad, v) {
            return {choice: v, taxa: _.pluck(taxad, 'id')};
        }).value();
        f.install_values({pile_taxa: this.pile_taxa, values: values});
        this.add(f);
    },

    add: function(filter) {
        this.get('filters').push(filter);
        this.get('filtermap')[filter.slug] = filter;
    },

    // Run the query, but return rather than persist the results.

    compute: function(skip_filter) {
        var taxa = this.get('pile_taxa');
        _.each(this.filters, function(f) {
            if (f !== skip_filter && f.value !== null) {
                var matches = f.taxa_matching().concat(f.valueless_taxa);
                taxa = _.intersect(taxa, matches);
            }
        });
        return _.sortBy(taxa, this.numsort);
    },

    // Run the query, saving the result so that observers get updates.

    update: function() {
        this.set('taxa', this.compute());
    }.observes('filters.@each.value'),

    numsort: function(a, b) {return a - b}

})});

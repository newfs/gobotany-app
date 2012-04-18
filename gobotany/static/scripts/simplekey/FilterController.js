define([
    'ember',
    'jquery',
    'underscore-min',
    'simplekey/Filter'
], function(x, $, x, Filter) {return Ember.Object.extend({

    init: function(args) {
        this.filters = {};
        this.pile_taxa = _.pluck(args.taxadata, 'id');
        this.build_category_filter('family', args.taxadata);
        this.build_category_filter('genus', args.taxadata);
    },

    build_category_filter: function(name, taxadata) {
        var f = new Filter({short_name: name, value_type: 'TEXT'});
        var values = _.chain(taxadata).groupBy(name).map(function(taxad, v) {
            return {choice: v, taxa: _.pluck(taxad, 'id')};
        }).value();
        f.install_values({pile_taxa: this.pile_taxa, values: values});
        this.add(f);
    },

    add: function(filter) {
        this.filters[filter.slug] = filter;
    }
})});

define([
    'ember-metal',
    'ember-runtime',
    'jquery',
    'underscore-min'
], function() {return Ember.Object.extend({

    init: function(args) {
        var slug = args.short_name;
        var is_length = (slug.indexOf('length') > -1) ||
            (slug.indexOf('width') > -1) ||
            (slug.indexOf('height') > -1) ||
            (slug.indexOf('thickness') > -1) ||
            (slug.indexOf('diameter') > -1);

        this.set('slug', slug)
            .set('value_type', args.value_type)
            .set('friendly_name', args.friendly_name)
            .set('hint', args.hint)
            .set('question', args.question)
            .set('image_url', args.image_url)
            .set('is_length', is_length)
            .set('value', null)
            .set('values', null)
            .set('choicemap', {});
    },

    /* Install the list of values returned by the API for this filter. */

    install_values: function(args) {
        var values = _.filter(args.values, function(v) {
            // Only keep values that have one or more taxa in this pile.
            return _.intersection(args.pile_taxa, v.taxa).length;
        });
        var alltaxa = [];
        var choicemap = {};
        _.each(values, function(value) {
            alltaxa = _.union(alltaxa, value.taxa);
            if (value.choice)
                choicemap[value.choice] = value;
        });
        this.set('values', values);
        this.set('choicemap', choicemap);
        this.set('valueless_taxa', _.difference(args.pile_taxa, alltaxa));
    }

})});

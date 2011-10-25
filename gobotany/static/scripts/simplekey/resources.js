/*
 * Async singletons.
 */
define([
    'jquery.tools.min',
    'underscore-min'
], function() {
    var module = {};

    /*
     * Simple AJAX requests.
     */
    module.key_vector = _.memoize(function(key_name) {
        return $.get(API_URL + 'vectors/key/' + key_name + '/');
    });
    module.pile_vector = _.memoize(function(pile_slug) {
        return $.get(API_URL + 'vectors/pile/' + pile_slug + '/');
    });
    /*
     * Functions that combine data from multiple AJAX requests.
     */
    module.species_vector = _.memoize(function(key_name, pile_slug) {
        var deferred = $.Deferred();
        $.when(
            module.key_vector(key_name),
            module.pile_vector(pile_slug)
        ).done(function(a, b) {
            deferred.resolve(_.intersect(a[0][0].species, b[0][0].species));
        });
        return deferred;
    });

    return module;
});

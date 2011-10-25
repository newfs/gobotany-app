/*
 * Async singletons.
 */
define([
    'jquery.tools.min',
    'underscore-min'
], function() {
    var module = {};

    /*
     * Return a Deferred for an AJAX request, which always simply
     * returns the data from the call.  An actual $.ajax() object, by
     * contrast, returns simple data to .get() but an awkward triple
     * [data, status, jqXHR] when passed through $.when().
     */
    module.get = function(path) {
        var d = $.Deferred();
        $.get(API_URL + path).done(function(r) {
            d.resolve(r);
        });
        return d;
    },
    /*
     * Simple AJAX requests.
     */
    module.character_vector = _.memoize(function(short_name) {
        return module.get('vectors/character/' + short_name + '/');
    });
    module.key_vector = _.memoize(function(key_name) {
        return module.get('vectors/key/' + key_name + '/');
    });
    module.pile_vector = _.memoize(function(pile_slug) {
        return module.get('vectors/pile/' + pile_slug + '/');
    });
    /*
     * Functions that combine data from multiple AJAX requests.
     */
    module.base_vector = _.memoize(function(key_name, pile_slug) {
        var deferred = $.Deferred();
        $.when(
            module.key_vector(key_name),
            module.pile_vector(pile_slug)
        ).done(function(kv, pv) {
            deferred.resolve(_.intersect(kv[0].species, pv[0].species));
        });
        return deferred;
    });

    simplekey_resources = module;  // global, for code still stuck in Dojo
    return module;
});

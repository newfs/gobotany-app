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
    module.get = function(path, data) {
        var d = $.Deferred();
        $.ajax({
            url: API_URL + path, data: data, traditional: true
        }).done(function(r) {
            d.resolve(r);
        });
        return d;
    },
    /*
     * Our AJAX resources.
     */

    module.pile_characters = _.memoize(function(pile_slug, character_names) {
        return module.get('piles/' + pile_slug + '/characters/', {
            include: character_names
        });
    });
    module.pile_best_characters = _.memoize(function(args) {
        return module.get('piles/' + args.pile_slug + '/characters/', {
            choose_best: 3,
            species_id: args.species_ids,
            character_group_id: args.character_group_ids,
            exclude: args.exclude_characters
        });
    });
    module.pile_species = _.memoize(function(pile_slug) {
        return module.get('species/' + pile_slug + '/');
    });

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

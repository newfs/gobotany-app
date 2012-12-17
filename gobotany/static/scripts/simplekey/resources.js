/*
 * Async singletons.
 */
define([
    'bridge/jquery',
    'bridge/underscore'
], function($, _) {
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

    module.glossaryblob = _.memoize(function() {
        return module.get('glossaryblob/');
    });

    module.pile = _.memoize(function(pile_slug) {
        return module.get('piles/' + pile_slug + '/');
    });
    module.pile_characters = _.memoize(function(pile_slug) {
        return module.get('piles/' + pile_slug + '/characters/');
    });
    module.more_questions = _.memoize(function(args) {
        return module.get('piles/' + args.pile_slug + '/questions/', {
            choose_best: 3,
            species_ids: args.species_ids.join('_'),
            character_group_id: args.character_group_ids,
            exclude: args.exclude_characters
        });
    },
        /* Custom hash function, so arguments that vary will always
         * be considered. The default hash function for memoize just
         * uses the first argument, which may have been the pile_slug. */
        function(args) {
            // Make a hash key out of the arguments that can vary.
            return args.exclude_characters + args.character_group_ids +
                   args.species_ids;
        }
    );
    module.pile_species = _.memoize(function(pile_slug) {
        return module.get('species/' + pile_slug + '/');
    });

    module.taxon_info = function(scientific_name) { // NOT memoized - save mem
        save_name = scientific_name.replace(' ', '%20');
        return module.get('taxa/' + save_name + '/');
    };

    module.character_vector = _.memoize(function(short_name) {
        return module.get('vectors/character/' + short_name + '/');
    });
    module.key_vector = _.memoize(function(key_name) {
        return module.get('vectors/key/' + key_name + '/');
    });
    module.pile_vector = _.memoize(function(pile_slug) {
        return module.get('vectors/pile/' + pile_slug + '/');
    });
    module.pile_set = _.memoize(function(pile_slug) {
        return module.get('vectors/pile-set/' + pile_slug + '/');
    });

    /*
     * Functions that combine data from multiple AJAX requests.
     */
    module.base_vector = _.memoize(function(args) {
        var deferred = $.Deferred();
        $.when(
            module.key_vector(args.key_name),
            module.pile_vector(args.pile_slug)
        ).done(function(kv, pv) {
            deferred.resolve(_.intersection(kv[0].species, pv[0].species));
        });
        return deferred;
    });

    simplekey_resources = module;  // global, for code still stuck in Dojo
    return module;
});

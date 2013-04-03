define([
    'bridge/handlebars',
    'bridge/jquery',
    'bridge/underscore',
    'simplekey/resources',
    'simplekey/utils',
    'util/glossarizer',
    'util/shadowbox_init'
], function(Handlebars, $, _, resources, utils, glossarizer, Shadowbox) {

    // A few characters get a "compact" list for multiple values.
    var COMPACT_EX = /^habitat|habitat_general|state_distribution$/;
    var MAX_CHARACTERS = 6;

    var glossarize = glossarizer.glossarize;
    var exports = {};

    exports.connect = function($anchor, scientific_name, pile_slug) {
        $anchor.click(function(event) {
            if ($(window).width() <= 600)
                return;  // follow the link directly to the species page
            _open_popup($anchor, scientific_name, pile_slug);
            return false;
        });
    };

    var _open_popup = function($anchor, scientific_name, pile_slug) {

        /* Call the API to get more information about the plant. */

        var plant_info_ready = resources.taxon_info(scientific_name);

        /* Figure out which piles will govern the characters to display. */

        var pile_slugs_ready = $.Deferred();

        if (pile_slug) {
            pile_slugs_ready.resolve([pile_slug]);
        } else {
            plant_info_ready.done(function(plant) {
                pile_slugs_ready.resolve(plant.pile_slugs);
            });
        }

        /* Once we know the list of piles, we can fetch them and then
           construct a list of characters to display by combining the
           characters from however many piles have been listed. */

        var characters_ready = $.Deferred();

        pile_slugs_ready.done(function(pile_slugs) {
            var pile_fetches = _.map(pile_slugs, function(pile_slug) {
                return resources.pile(pile_slug);
            });
            $.when.apply($, pile_fetches).done(function() {
                var arrays = _.pluck(arguments, 'plant_preview_characters');
                var characters = _.map(_.flatten(arrays), _.clone);
                _remove_duplicate_characters(characters);
                characters_ready.resolve(characters);
            });
        });

        $.when(
            plant_info_ready,
            characters_ready
        ).done(function(plant, characters) {
            _finally_open_popup($anchor, plant, characters);
        });
    };

    var _finally_open_popup = function($anchor, plant, characters) {

        characters = _.chain(characters)
            .filter(_filter_character, {plant: plant})
            .first(MAX_CHARACTERS)
            .value();

        _put_clicked_image_first(plant, $anchor);

        var source = $('#plantpreview-popup-template').html().trim();
        var template = Handlebars.compile(source);
        var popup_html = template({
            characters: characters,
            plant: plant,
            plant_url: $anchor.attr('href')
        });

        Shadowbox.open({
            content: popup_html,
            player: 'html',
            height: 520,
            width: 935,
            options: {
                handleOversize: 'resize',
                onFinish: function() {
                    var $sb = $('#sb-container');
                    var $children = $sb.find('p, dt, dd, li');
                    $sb.find('.img-container').scrollable();
                    glossarize($children);
                }
            }
        });
    };

    var _remove_duplicate_characters = function(characters) {
        var seen = {};
        var i = 0;
        while (i < characters.length) {
            var csn = characters[i].character_short_name;
            if (_.has(seen, csn)) {
                characters.splice(i, 1)
            } else {
                seen[csn] = true;
                i++;
            }
        }
    };

    var _filter_character = function(character) {
        /* Decide whether to display this character; if so, mark up the
           character with how we should display its value. */

        var plant = this.plant;

        /* Display any character regardless of partner for now, because we
         * are not yet importing preview characters for partner sites.
         * (They are likely configurable in the Admin, though.)
         * TODO: make the API return only the preview characters for the
         * partner specified in the URL rather than having a
         * .partner_site field with the character. It looks like it will
         * be easier to accomplish this if moving the API code out of
         * handlers.py, because the Piston-based static method for
         * plant_preview_characters will need to have the request object
         * handy in order to call which_partner for the partner name.
         */
        /* Update: gobotany_sk_partner_site has now been removed, so
         * partner name will need to be gotten differently if needed */
        //if (character.partner_site != gobotany_sk_partner_site)
        //    return false;

        var short_name = character.character_short_name
        var value = plant[short_name];
        if (typeof value === 'undefined' || !value)
            return false;

        if (character.value_type === 'LENGTH') {
            var unit = character.unit;
            var min = value[0];
            var max = value[1];
            var min_mm = utils.convert(min, unit, 'mm');
            var max_mm = utils.convert(max, unit, 'mm');
            value = (
                utils.pretty_length(unit, min_mm, false) + '&#8211;' +
                    utils.pretty_length(unit, max_mm)
            );
        }

        if (!value)
            return false;

        character.display_value = value;
        character.is_sequence = (typeof(value) !== 'string');
        character.is_compact = COMPACT_EX.test(short_name);
        return true;
    };

    var _put_clicked_image_first = function(plant, $anchor) {
        var clicked_image_url = $anchor.find('img').attr('src');
        if (typeof clicked_image_url === 'undefined')
            return;
        var basename = function(url) {
            return url.match(/[^\/]*$/)[0]
        };
        var name = basename(clicked_image_url);
        plant.images.sort(function(image) {
            return basename(image.url) == name ? 0 : 1;
        });
    };

    return exports;
});

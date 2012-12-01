define([
    'bridge/handlebars',
    'bridge/jquery',
    'bridge/underscore',
    'simplekey/resources',
    'simplekey/utils',
    'util/glossarizer',
    'util/shadowbox_init'
], function(Handlebars, $, _, resources, utils, glossarizer, Shadowbox) {

    var MAX_CHARACTERS = 6;

    var glossarize = glossarizer.glossarize;
    var exports = {};

    exports.connect = function($anchor, scientific_name) {
        $anchor.click(function(event) {
            if ($(window).width() <= 600)
                return;  // follow the link directly to the species page
            _open_popup($anchor, scientific_name);
            return false;
        });
    };

    var _open_popup = function($anchor, scientific_name, pile_slug) {

        // A few characters get a "compact" list for multiple values.
        var COMPACT_EX = /^habitat|habitat_general|state_distribution$/;

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
                var characters = _.flatten(arrays);
                _remove_duplicate_characters(characters);
                characters_ready.resolve(characters);
            });
        });

        $.when(
            plant_info_ready,
            characters_ready
        ).done(function(plant, characters) {

            // // Fill in Characteristics.
            // var $characteristics = $(
            //     '#plant-detail-modal .details .characteristics');
            // $characteristics.empty();

            // var characters_html = '';
            // var characters_displayed = 0;
            // for (var i = 0; i < characters.length; i++) {
            //     var ppc = characters[i];

            //     if (ppc.partner_site === gobotany_sk_partner_site) {

            //         var display_value = '';
            //         var character_value =
            //             taxon[ppc.character_short_name];
            //         if (character_value !== undefined &&
            //             character_value !== null) {

            //             display_value = character_value;
            //             if (ppc.value_type === 'LENGTH') {
            //                 var min = character_value[0];
            //                 var max = character_value[1];
            //                 var min_mm = utils.convert(
            //                     min, ppc.unit, 'mm');
            //                 var max_mm = utils.convert(
            //                     max, ppc.unit, 'mm');
            //                 display_value =
            //                     utils.pretty_length(
            //                         ppc.unit, min_mm, false) + '&#8211;' +
            //                     utils.pretty_length(
            //                         ppc.unit, max_mm);
            //             }
            //             else {
            //                 // For multiple-value characters,
            //                 // make a list.
            //                 if (typeof(display_value) !== 'string') {
            //                     var is_compact = (COMPACT_EX.test(
            //                         ppc.character_short_name));
            //                     display_value = _get_multivalue_list(
            //                         display_value, is_compact);
            //                 }
            //             }
            //         }

            //         // Only display this character if it has a value
            //         // and if the maximum number of characters for the
            //         // popup has not been exceeded.

            //         if (display_value !== undefined &&
            //             display_value !== '') {

            //             $characteristics.append(
            //                 $('<dl>').append(
            //                     $('<dt>', {html: ppc.friendly_name}),
            //                     $('<dd>').append(display_value)
            //                 )
            //             );

            //             characters_displayed += 1;
            //             if (characters_displayed >= MAX_CHARACTERS)
            //                 break;
            //         }
            //     }
            // }

            _put_clicked_image_first(plant, $anchor);

            var source = $('#plantpreview-popup-template').html().trim();
            var template = Handlebars.compile(source);
            var popup_html = template({
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

    var _get_multivalue_list = function(display_value, is_compact) {

        // Return a HTML list for presenting multiple character values.
        if (typeof(display_value) === 'string')
            return display_value;

        var $ul = $('<ul>');
        if (is_compact)
            $ul.addClass('compact');

        var $li = null;
        _.each(display_value, function(v) {
            $li = $('<li>', {'html': v}).appendTo($ul);
        });

        if ($li !== null)
            $li.addClass('last');

        return $ul;
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

define([
    'bridge/jquery',
    'bridge/underscore',
    'simplekey/resources'
], function(
    $, _, resources
) {
    exports = {};

    // var group_names;            // character groups
    var characters;             // raw data from the API

    var $p;                     // paragraph around button
    var $button;                // "Get More Choices" button
    var $ul = null;             // <ul> of character groups

    exports.install_handlers = function(pile_slug, filter_controller) {
        resources.pile_set(pile_slug).done(function(data) {
            characters = data;
            compute_coverage_lists();

            // group_names = _.uniq(_.pluck(characters, 'group_name'));
            // group_names.sort();

            $p = $('#sidebar .get-more');
            $button = $p.find('.get-choices');

            $button.on('click', toggle_group_list);
            $p.on('mouseenter', 'li', display_group_of_characters);

            sort_remaining_characters();
        });
    };

    /* Figure out the full list of taxa covered by each character. */

    var compute_coverage_lists = function() {
        for (var i = 0; i < characters.length; i++) {
            var character = characters[i];
            var values = character.values;
            character.taxon_ids_covered = _.intersection(values);
        }
    };

    var do_huge_computation = function() {
        for (var i = 0; i < characters.length; i++) {
            var character = characters[i];
            var values = character.values;
            var all_taxon_ids = values.length ? values[0] : [];

            for (var j = 1; j < values.length; j++) {
                var taxon_ids = values[j];
                all_taxon_ids;
                var xids = _.intersection(taxon_ids, taxon_ids);
                // console.log(taxon_ids);
            }
        }
    };

    var sort_remaining_characters = function() {
        return _.chain(characters)
            .sortBy('ease')
            .sortBy(function(character) {
                return 1;
            })
            .sortBy('group_name')
            .value();
    };

    /* API routines. */

    var toggle_group_list = function(event) {

        if (! $button.is(event.target))
            return;

        if ($ul === null) {
            var remaining_characters = sort_remaining_characters();
            var group_name = null;
            var $group_ul;

            $ul = $('<ul>').addClass('get-more-questions-menu');
            $ul.appendTo('.get-more');

            _.each(remaining_characters, function(character) {
                if (character.group_name != group_name) {
                    group_name = character.group_name;
                    $group_ul = $('<ul>').appendTo(
                        $('<li>').text(group_name + ' ▸').appendTo($ul));
                }
                $group_ul.append($('<li>').text(
                    character.ease + ' ' + character.name));
            });
        } else {
            $ul.remove();
            $ul = null;
        }
    };

    var display_group_of_characters = function() {
        var $ul_beneath = $(this).find('ul');
        if ($ul_beneath.length) {
            $p.find('ul ul').hide();
            $ul_beneath.show();
        }
    };

    return exports;
});

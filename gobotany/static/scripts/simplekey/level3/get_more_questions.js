define([
    'bridge/jquery',
    'bridge/underscore',
    'simplekey/resources'
], function(
    $, _, resources
) {
    exports = {};

    var group_names;            // character groups
    var characters;             // raw data from the API

    var $button;                // "Get More Choices" button
    var $group_list = null;     // <ul> of character groups
    var $character_list = null; // <ul> of characters

    exports.install_handlers = function(pile_slug) {
        resources.pile_set(pile_slug).done(function(data) {
            characters = data;
            group_names = _.uniq(_.pluck(characters, 'group_name'));
            group_names.sort();

            console.log(data.length);

            $button = $('#sidebar .get-choices');
            $button.on('click', toggle_group_list);
        });
    };

    var toggle_group_list = function() {
        console.log('!');
        if ($group_list === null) {
            $group_list = $('<ul>').appendTo($button);
            _.each(group_names, function(group_name) {
                $('<li>').text(group_name + ' ▸').appendTo($group_list);
            });
        } else {
            ; /* hide */
        }
    };

    return exports;
});

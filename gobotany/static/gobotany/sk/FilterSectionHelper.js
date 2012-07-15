define([
    'dojo/_base/declare',
    'bridge/jquery'
], function(declare, $) {
return declare('gobotany.sk.FilterSectionHelper', null, {

    _setup_character_groups: function(character_groups) {
        var $ul = $('ul.char-groups').empty();
        _.each(character_groups, function(character_group) {
            $ul.append(
                $('<li>').append(
                    $('<label>').append(
                        $('<input>', {type: 'checkbox',
                                      value: character_group.id}),
                        ' ' + character_group.name
                    )
                )
            );
        });
    }
});
});

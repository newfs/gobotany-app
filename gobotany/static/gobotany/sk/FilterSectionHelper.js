define([
    'dojo/_base/declare',
    'dojo/_base/lang',
    'dojo/query',
    'dojo/dom-construct',
    'bridge/jquery'
], function(declare, lang, query, domConstruct,
            $) {
return declare('gobotany.sk.FilterSectionHelper', null, {

    _setup_character_groups: function(character_groups) {
        console.log('FilterSectionHelper: Updating character groups');

        var character_groups_list = query('ul.char-groups')[0];
        domConstruct.empty(character_groups_list);
        var i;
        for (i = 0; i < character_groups.length; i++) {
            var character_group = character_groups[i];
            var item = domConstruct.create('li', { innerHTML: '<label>' +
                '<input type="checkbox" value="' + character_group.id +
                '"> ' + character_group.name + '</label>'});
            domConstruct.place(item, character_groups_list);
        }
    }
});
});

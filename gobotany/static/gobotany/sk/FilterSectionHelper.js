define([
    'dojo/_base/declare',
    'dojo/_base/lang',
    'dojo/query',
    'dojo/dom-construct',
    'bridge/jquery',
    'util/sidebar',
    'gobotany/sk/working_area'
], function(declare, lang, query, domConstruct, $, sidebar, working_area) {
return declare('gobotany.sk.FilterSectionHelper', null, {
    working_area: null,

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
    },

    /* A filter object has been returned from Ajax!  We can now set up
       the working area and save the new page state. */

    show_filter_working_onload: function(filter, y) {
        // Dismiss old working area, to avoid having an Apply button
        // that is wired up to two different filters!
        if (this.working_area !== null)
            this.working_area.dismiss();

        var C = working_area.select_working_area(filter);

        this.working_area = C({
            div: $('div.working-area')[0],
            filter: filter,
            y: y,
            on_dismiss: lang.hitch(this, 'on_working_area_dismiss')
        });

        sidebar.set_height();
    },

    /* When the working area is dismissed, we clean up and save state. */

    on_working_area_dismiss: function(filter) {
        this.working_area = null;

        // Clear selected state in the questions list at left.
        $('.option-list li').removeClass('active');
    }
});
});

dojo.provide('gobotany.sk.guided_search');

dojo.require('dojox.data.JsonRestStore');
dojo.require('gobotany.filters');

dojo.declare('gobotany.sk.guided_search.GuidedSearchManager', null, {

    constructor: function() {
        this.store = new dojox.data.JsonRestStore({
            target: '/characters/',
        });
        this.filter_manager = new gobotany.filters.FilterManager({});
        this.store.fetch({
            scope: this,
            onComplete: this.save_character_groups,
        });
    },

    save_character_groups: function(data) {
        this.character_groups = data;
        this.add_filter();
    },

    add_filter: function() {
        var node = dojo.query('#character_list')[0];
        var select = dojo.create('select', {}, node);
        for (var i=0; i < this.character_groups.length; i++) {
            var group = this.character_groups[i];
            li = dojo.create('option', {
                value: group.short_name,
            }, select);
            li.innerHTML = group.name;
        }
    },

})

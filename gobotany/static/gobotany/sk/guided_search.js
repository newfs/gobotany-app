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
            onComplete: this.save_character_list,
        });
    },

    save_character_list: function(data) {
        this.character_list = data;
        this.add_filter();
    },

    add_filter: function() {
        var node = dojo.query('#character_list')[0];
        for (var i=0; i < this.character_list.length; i++) {
            li = dojo.create('li', {}, node);
            li.innerHTML = this.character_list[i].name;
        }
    },

})

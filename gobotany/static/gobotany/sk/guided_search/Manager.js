dojo.provide('gobotany.sk.guided_search.Manager');

dojo.require('dojox.data.JsonRestStore');
dojo.require('gobotany.filters');
dojo.require('gobotany.sk.guided_search.Filter');
dojo.require('gobotany.sk.guided_search.SpeciesSectionHelper');

dojo.declare('gobotany.sk.guided_search.Manager', null, {

    constructor: function() {
        this.filters = [];
        this.character_group_list = [];
        this.character_group_map = {};
        this.filter_manager = new gobotany.filters.FilterManager({});
        this.species_manager =
            new gobotany.sk.guided_search.SpeciesSectionHelper(this);
        this.species_manager.setup_section();
        this.store = new dojox.data.JsonRestStore({
            target: '/characters/'
        });
        this.store.fetch({
            scope: this,
            onComplete: this.save_character_groups
        });

        dojo.query('#plants .species_count .loading').addClass('hidden');
        dojo.query('#plants .species_count .count').addClass('hidden');
    },

    save_character_groups: function(data) {
        this.character_group_list = data;
        for (i = 0; i < this.character_group_list.length; i++) {
            var character_group = this.character_group_list[i];
            this.character_group_map[character_group.name] = character_group;
        }
        this.add_filter();
    },

    add_filter: function() {
        var node = dojo.query('#filter_list')[0];
        var div = dojo.create('div', {}, node);
        var filter = gobotany.sk.guided_search.Filter(this, div);
        this.filters.push(filter);
    },

    perform_query: function() {
        var fm = this.filter_manager;

        if (fm.filters.length > 0) {
            this.species_manager.perform_query();
        } else {
            dojo.empty('plant-listing');
            this.species_manager.on_complete_perform_query({items: []});
        }
    },

    save_filter_state: function() {
        /* function called by the SpeciesSectionHelper */
    }
});

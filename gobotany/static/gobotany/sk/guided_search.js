dojo.provide('gobotany.sk.guided_search');

dojo.require('dojox.data.JsonRestStore');
dojo.require('gobotany.filters');

dojo.declare('gobotany.sk.guided_search.Manager', null, {

    constructor: function() {
        this.filters = [];
        this.character_group_list = [];
        this.character_group_map = {};
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
        this.character_group_list = data;
        for (i=0; i < this.character_group_list.length; i++) {
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

});

dojo.declare('gobotany.sk.guided_search.Filter', null, {

    constructor: function(manager, parentnode) {
        this.manager = manager;
        this.parentnode = parentnode;

        this.character_group_select = dojo.create('select', {}, parentnode);
        this.character_select = dojo.create('select', {}, parentnode);
        this.character_value_select = dojo.create('select', {}, parentnode);

        dojo.connect(this.character_group_select, 'onchange', this,
                     this.on_character_group_select);
        dojo.connect(this.character_select, 'onchange', this,
                     this.on_character_select);
        dojo.connect(this.character_value_select, 'onchange', this,
                     this.on_character_value_select);

        this.setup_character_group();
        this.deactivate_character();
        this.deactivate_character_value();
    },

    deactivate_character: function() {
        var s = this.character_select;
        while (s.hasChildNodes()) {
            s.removeChild(s.lastChild);
        }
        var option = dojo.create('option', {}, s);
        option.innerHTML = 'Character';
        s.disabled = 'true';
    },

    deactivate_character_value: function() {
        var s = this.character_value_select;
        while (s.hasChildNodes()) {
            s.removeChild(s.lastChild);
        }
        var option = dojo.create('option', {}, s);
        option.innerHTML = 'Character value';
        s.disabled = 'true';
    },

    setup_character_group: function () {
        var s = this.character_group_select;
        var list = this.manager.character_group_list;
        for (i=0; i < list.length; i++) {
            var character_group = list[i];
            var option = dojo.create('option', {
                value: character_group.name,
                innerHTML: character_group.name,
            }, s);
        }
    },

    setup_character: function () {
        var cgs = this.character_group_select;
        var cgname = cgs.options[cgs.selectedIndex].value;
        var character_group = this.manager.character_group_map[cgname];
        var characters = character_group.characters;

        var s = this.character_select;
        while (s.hasChildNodes()) {
            s.removeChild(s.lastChild);
        }
        for (var i=0; i < characters.length; i++) {
            var character = characters[i];
            var option = dojo.create('option', {
                value: character.short_name,
            }, s);
            option.innerHTML = character.name;
        }
        s.removeAttribute('disabled');
    },

    setup_character_value: function () {
        ;
    },

    on_character_group_select: function (event) {
        this.deactivate_character_value();
        this.setup_character();
    },

    on_character_select: function (event) {
        this.setup_character_value();
    },

    on_character_value_select: function (event) {
        ;
    },

});

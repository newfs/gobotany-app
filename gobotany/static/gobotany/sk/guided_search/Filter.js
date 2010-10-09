dojo.provide('gobotany.sk.guided_search.Filter');

dojo.declare('gobotany.sk.guided_search.Filter', null, {

    constructor: function(manager, parentnode) {
        this.manager = manager;
        this.parentnode = parentnode;
        this.filter_short_name = '';
        this.filter_value_str = '';

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
        this.setup_character();
        this.setup_character_value();
    },

    setup_character_group: function() {
        var s = this.character_group_select;
        var list = this.manager.character_group_list;
        var option = dojo.create('option', {
            value: '',
            innerHTML: '&lt;Select character group&gt;'
        }, s);
        for (i = 0; i < list.length; i++) {
            var character_group = list[i];
            var option = dojo.create('option', {
                value: character_group.name,
                innerHTML: character_group.name
            }, s);
        }
    },

    setup_character: function() {
        var s = this.character_select;

        while (s.hasChildNodes()) {
            s.removeChild(s.lastChild);
        }
        var option = dojo.create('option', {
            value: '',
            innerHTML: '&lt;Select character&gt;'
        }, s);

        var cgs = this.character_group_select;
        var cgname = cgs.options[cgs.selectedIndex].value;

        if (cgname == '') {
            s.disabled = 'true';
            return;
        }

        var character_group = this.manager.character_group_map[cgname];
        var characters = character_group.characters;

        for (var i = 0; i < characters.length; i++) {
            var character = characters[i];
            var option = dojo.create('option', {
                value: character.short_name,
                innerHTML: character.name
            }, s);
        }
        s.removeAttribute('disabled');
    },

    setup_character_value: function() {
        var s = this.character_value_select;

        while (s.hasChildNodes()) {
            s.removeChild(s.lastChild);
        }
        var option = dojo.create('option', {
            value: '',
            innerHTML: '&lt;Select value&gt;'
        }, s);

        var cs = this.character_select;
        var short_name = cs.options[cs.selectedIndex].value;
        if (short_name == '') {
            s.disabled = 'true';
            return;
        }

        this.manager.store.fetch({
            scope: this,
            query: short_name + '/',
            onComplete: function(character_value_list) {

                for (var i = 0; i < character_value_list.length; i++) {
                    var character_value = character_value_list[i];
                    if (character_value.value_str == 'NA')
                        continue;
                    var option = dojo.create('option', {
                        value: character_value.value_str,
                        innerHTML: character_value.value_str
                    }, s);
                }

                s.removeAttribute('disabled');
            }
        });
    },

    setup_filter: function() {
        var cs = this.character_select;
        var cvs = this.character_value_select;

        var short_name;
        cs.selectedIndex;
        cvs.options;
        cvs.options[cs.selectedIndex];
        var value_str = cvs.options[cvs.selectedIndex].value;
        if (value_str == '')
            short_name = '';
        else
            short_name = cs.options[cs.selectedIndex].value;

        if (this.filter_short_name == short_name &&
            this.filter_value_str == value_str)
            return;

        var fm = self.manager.filter_manager;

        if (this.filter_short_name != short_name) {
            if (this.filter_short_name != '')
                fm.remove_filter(this.filter_short_name);
            if (short_name != '')
                fm.add_filter({ character_short_name: short_name });
        }

        this.filter_short_name = short_name;
        this.filter_value_str = value_str;
        if (short_name != '')
            fm.set_selected_value(short_name, value_str);

        if (fm.filters.length > 0) {
            fm.perform_query({
                filter_short_names: [],
                on_complete: function(data) {
                    var t = dojo.query('#guided_search_total')[0];
                    t.innerHTML = '' + data.items.length + ' species';
                }
            });
        } else {
            var t = dojo.query('#guided_search_total')[0];
            t.innerHTML = '';
        }
    },

    on_character_group_select: function(event) {
        this.setup_character();
        this.setup_character_value();
        this.setup_filter();
    },

    on_character_select: function(event) {
        this.setup_character_value();
        this.setup_filter();
    },

    on_character_value_select: function(event) {
        this.setup_filter();
    }

});

// UI code for the Simple Key results/filter page.

// Global declaration for JSLint (http://www.jslint.com/)
/*global console, dojo, dojox, gobotany */

dojo.provide('gobotany.sk.results');

dojo.require('gobotany.sk.RulerSlider');
dojo.require('gobotany.sk.glossarize');
dojo.require('gobotany.sk.results.SpeciesSectionHelper');
dojo.require('gobotany.filters');
dojo.require('gobotany.piles');
dojo.require('gobotany.utils');

dojo.require('dojo.cookie');
dojo.require('dojo.hash');
dojo.require('dojo.html');
dojo.require('dojo.data.ItemFileWriteStore');
dojo.require('dijit.Dialog');
dojo.require('dijit.form.Button');
dojo.require('dijit.form.CheckBox');
dojo.require("dijit.form.FilteringSelect");
dojo.require('dijit.form.Form');
dojo.require('dijit.form.Select');

dojo.declare('gobotany.sk.results.ResultsHelper', null, {
    slider_node: null,
    ruler: null,

    constructor: function(/*String*/ pile_slug) {
        // summary:
        //   Helper class for managing the sections on the results page.
        // description:
        //   Coordinates all of the dynamic logic on the results page.
        //   The procedure for using this class is to instantiate it
        //   and then call it's setup() method.
        // | var helper = new gobotany.sk.results.ResultsHelper('some_pile');
        // | helper.setup();

        this.pile_slug = pile_slug;
        this.pile_manager = new gobotany.piles.PileManager(this.pile_slug);
        this.filter_manager = new gobotany.filters.FilterManager({
            pile_slug: this.pile_slug
        });
   },

    setup: function() {
        // summary:
        //   Sets up the results page with appropriate callbacks
        // description:
        //   Connects callback functionality and generally sets up
        //   the logic of the page ready for use, this should only
        //   be called once.

        console.log('ResultsHelper: setting up page - ' + this.pile_slug);

        this.species_section = new gobotany.sk.results.SpeciesSectionHelper(this);
        this.species_section.setup_section();

        this.filter_section = new gobotany.sk.results.FilterSectionHelper(this);
        this.filter_section.setup_section();

        // Wire up the filter working area's close button.
        var el = dojo.query('#filter-working .close')[0];
        dojo.connect(el, 'onclick', null, 
                     dojo.hitch(this, this.filter_section.hide_filter_working));

        dojo.subscribe("results_loaded", dojo.hitch(this, this.populate_image_types));

        // Update images on selction change
        var select_box = dijit.byId('image-type-selector');
        dojo.connect(select_box, 'onChange',
                     dojo.hitch(this, this.load_selected_image_type));

        dojo.connect(this.pile_manager, 'on_pile_info_changed', dojo.hitch(this, function(pile_info) {
            this.filter_section._setup_character_groups(pile_info.character_groups);

            this.filter_manager.plant_preview_characters =
                pile_info.plant_preview_characters;

            // a hash means filter state has been set, don't load up the default filters for a pile if
            // filter state has already been set

            var complete = dojo.hitch(this, function(filters) {
                this.save_filter_state();

                var watcher = new gobotany.filters.FilterLoadingWatcher(filters);
                watcher.load_values({on_values_loaded: dojo.hitch(this, function(filters) { 
                    this.filter_section.display_filters(filters);
                    this.filter_section.update_filter_display('family');
                    this.filter_section.update_filter_display('genus');

                    dojo.query('#filters .loading').addClass('hidden');
                    this.species_section.perform_query();
                })});
            });

            this.filter_section.add_callback_filters();

            if (dojo.hash()) {
                this.setup_filters_from_hash({on_complete: complete});
            } else {
                this.setup_filters_from_pile_info({on_complete: complete});
            }

        }));
        this.pile_manager.load();

        this.setup_onhashchange();
    },
    
    setup_onhashchange: function() {
        // Set up the onhashchange event handler, which will be used to detect
        // Back button undo events for modern browsers.
        dojo.connect(document.body, 'onhashchange', this, this.handle_undo,
                     true);
    },

    handle_undo: function() {
        // Detect and handle URL hash changes for which Undo is supported.
        var current_url = window.location.href;

        var last_plant_id_url = dojo.cookie('last_plant_id_url');
        if (last_plant_id_url === undefined) {
            last_plant_id_url = '';
        }

        // When going forward and applying values, etc., the current URL and
        // last plant ID URL are always the same. After pressing Back, they
        // are different.
        if (current_url !== last_plant_id_url) {
            // Now reload the current URL, which reloads everything on the
            // page and sets it up all again. This means a little more going
            // on that usually seen with an Undo command, but is pretty
            // quick and allows for robust yet uncomplicated Undo support.
            window.location.reload();
        }
    },

    setup_filters_from_pile_info: function(args) {
        // summary:
        //   Sets up the internal filter data structure based on default
        //   filters in the pile info.

        var pile_info = this.pile_manager.pile_info;
        var filters = [];
        for (var x = 0; x < pile_info.default_filters.length; x++) {
            var obj = pile_info.default_filters[x];
            obj.pile_slug = this.pile_slug;
            var filter = this.filter_manager.add_filter(pile_info.default_filters[x]);
            filters.push(filter);
        }

        if (args && args.on_complete) {
            args.on_complete(filters);
        }
    },

    setup_filters_from_hash: function(args) {
        // summary:
        //   Sets up the internal filter data structure based on values in
        //   in the url hash (dojo.hash())

        console.log('setting up from hash - ' + dojo.hash());

        var hash_object = dojo.queryToObject(dojo.hash());
        if (hash_object['_filters'] === undefined) {
            return;
        }

        var comma = hash_object['_filters'].split(',');
        var filter_values = {};
        var filter_names = [];
        for (var x = 0; x < comma.length; x++) {
            var char_name = comma[x];
            var value = hash_object[char_name];
            if (this.filter_manager.has_filter(char_name)) {
                this.filter_manager.set_selected_value(char_name, value);
            }
            else {
                filter_values[char_name] = value;
                filter_names.push(comma[x]);
            }
        }

        this.filter_manager.query_filters({
            short_names: filter_names,
            onLoaded: dojo.hitch(this, function(items) {
                var filters = [];
                dojo.forEach(items, dojo.hitch(this, function(item) {
                    var filter_args = gobotany.utils.clone(item,
                        {pile_slug: this.pile_slug});
                    var filter = this.filter_manager.add_filter(filter_args);
                    filters.push(filter);
                    var name = filter.character_short_name;
                    var v = filter_values[name];
                    if (v !== undefined) {
                        this.filter_manager.set_selected_value(name, v);
                    }
                }));
                if (args && args.on_complete) {
                    args.on_complete(filters);
                }
            })
        });
    },

    save_filter_state: function() {
        // summary:
        //   Saves the state of the filters in a cookie and in the url hash.
        var LAST_URL_COOKIE_NAME = 'last_plant_id_url';

        console.log('saving filter info in url and cookie');
        
        // Retain the previous state, for supporting Undo.
        //var previous_url = dojo.cookie(LAST_URL_COOKIE_NAME);
        //if (previous_url === undefined) {
        //    previous_url = '';
        //}
        //dojo.cookie('previous_plant_id_url', previous_url, {path: '/'});
        
        // Save the current state.
        dojo.hash(this.filter_manager.as_query_string());
        dojo.cookie(LAST_URL_COOKIE_NAME, window.location.href, {path: '/'});
    },

    load_selected_image_type: function (event) {
        var image_type = dijit.byId('image-type-selector').value;
        var images = dojo.query('#plant-listing li img');
        // Replace the image for each plant on the page
        for (var i=0; i < images.length; i++) {
            var image = images[i];
            // Fetch the species for the current image
            this.filter_manager.result_store.fetchItemByIdentity({
                scope: {image: image,
                        image_type: image_type},
                identity: dojo.attr(image, 'x-plant-id'),
                onItem: function(item) {
                    var new_image;
                    // Search for an image of the correct type
                    for (var j=0; j < item.images.length; j++) {
                        if (item.images[j].type == image_type) {
                            new_image = item.images[j];
                            break;
                        }
                    }
                    if (new_image) {
                        // Replace either src or x-tmp-src depending on
                        // whether the current image has already been
                        // loaded.  This may result in a significant
                        // performance impact on large result sets
                        // which have already been scrolled before
                        // changing image types.  The alternative would
                        // be to unload previously loaded image pages.
                        var src_var = dojo.attr(image, 'x-tmp-src') ? 'x-tmp-src' : 'src';
                        dojo.attr(image, src_var, new_image.thumb_url);
                        dojo.attr(image, 'alt', new_image.title);
                        // Hide the empty box if it exists and make
                        // sure the image is visible.
                        dojo.query('+ span.MissingImage', image).orphan();
                        dojo.style(image, 'display', 'inline');
                    } else if (dojo.style(image, 'display') != 'none') {
                        // If there's no matching image display the
                        // empty box and hide the image
                        dojo.style(image, 'display', 'none');
                        dojo.create('span', {'class': 'MissingImage'}, image, 'after');
                    }
                }
            });
        }
    },

    // A subscriber for results_loaded
    populate_image_types: function(message) {
        var results = message.data.items;
        var select_box = dijit.byId('image-type-selector');
        // clear the select
        select_box.options.length = 0;
        // image types depend on the pile, we get the allowed values from
        // the result set for now
        var image_types = new Array();
        for (var i=0; i < results.length; i++) {
            var images = results[i].images;
            for (var j=0; j < images.length; j++) {
                var image_type = images[j].type;
                if (image_types.indexOf(image_type) == -1) {
                    image_types.push(image_type);
                }
            }
        }
        // sort lexicographically
        image_types.sort();
        for (i=0; i < image_types.length; i++) {
            var image_type = image_types[i];
            select_box.addOption({value: image_type,
                label: image_type});
            // Habit is selected by default
            if (image_type == 'habit') {
                select_box.attr('value', 'habit');
            }
        }
    }
});


dojo.declare('gobotany.sk.results.FilterSectionHelper', null, {
    constructor: function(results_helper) {
        // summary:
        //   Manages the filters section of the results page (including
        //   the genus/family filters).
        // results_helper:
        //   An instance of gobotany.sk.results.ResultsHelper

        this.results_helper = results_helper;
        this.glossarizer = gobotany.sk.results.Glossarizer();

        // This variable is for keeping track of which filter is currently
        // visible in the filter working area (if any).
        this.visible_filter_short_name = null;
    },

    setup_section: function() {
        console.log('FilterSectionHelper: setting up section');
        // Wire up the "More filters" button.
        var form = dijit.byId('more_filters_form');
        dojo.connect(form, 'onSubmit', this, function(event) {
            dojo.stopEvent(event);
            this.query_best_filters();
        });

        // Wire up the Apply button in the filter working area.
        var apply_button = dojo.query('#character_values_form button')[0];
        dojo.connect(apply_button, 'onclick', this, this._apply_filter);

        // Wire up the Family and Genus submit buttons.
        var family_store = new dojo.data.ItemFileWriteStore(
            {data: { label: 'name', identifier: 'family', items: [] }});
        
        var genus_store = new dojo.data.ItemFileWriteStore(
            {data: { label: 'name', identifier: 'genus', items: [] }});

        var family_select = dijit.byId('family_select');
        family_select.set('required', false);
        family_select.set('store', family_store);
        dojo.connect(family_select, 'onChange', this,
                     this.apply_family_filter);

        var genus_select = dijit.byId('genus_select');
        genus_select.set('required', false);
        genus_select.set('store', genus_store);
        dojo.connect(genus_select, 'onChange', this,
                     this.apply_genus_filter);

        // Wire up the "Clear" buttons for the family and genus.
        dojo.connect(dijit.byId('clear_family'), 'onClick', this,
                     this.clear_family);
        dojo.connect(dijit.byId('clear_genus'), 'onClick', this,
                     this.clear_genus);
    },

    _setup_character_groups: function(character_groups) {
        console.log('FilterSectionHelper: Updating char groups');
        var my_form = dojo.query('#more_filters form div')[0];
        var menu = dijit.byId('character_groups_menu');

        for (var i = 0; i < character_groups.length; i++) {
            var character_group = character_groups[i];
            var item = new dijit.CheckedMenuItem({label: character_group.name,
                                                  value: character_group.id});
            menu.addChild(item);
        }
    },

    query_best_filters: function() {
        var filter_manager = this.results_helper.filter_manager;

        console.log('FilterSectionHelper: getting more filters...');

        var form = dijit.byId('more_filters_form');
        var button = dijit.byId('get_more_filters_button');
        button.set('disabled', true);
        
        var menu = dijit.byId('character_groups_menu');
        var character_group_ids = [];
        for (var x = 0; x < menu.getChildren().length; x++) {
            var item = menu.getChildren()[x];
            if (item.checked)
                character_group_ids.push(item.value);
        }

        var existing = [];
        for (var x = 0; x < filter_manager.filters.length; x++)
            existing.push(filter_manager.filters[x].character_short_name);
        filter_manager.query_best_filters({
            character_group_ids: character_group_ids,
            existing_characters: existing,
            onLoaded: dojo.hitch(this, function(items) {
                if (items.length > 0) {
                    // Add the new filters to the Filter Manager.
                    new_filter_names = [];
                    dojo.forEach(items, function(filter_json) {
                        filter_manager.add_filter(filter_json);
                        new_filter_names.push(filter_json.short_name);
                    });
                    
                    // Get all the newly added filters, so they can be
                    // listed on the page and so their values can be loaded.
                    new_filters = [];
                    for (var i = 0; i < new_filter_names.length; i++) {
                        new_filters.push(filter_manager.get_filter(
                            new_filter_names[i]));
                    }

                    // Add the new filters to the filters list.
                    var added = this.display_filters(new_filters, 0);
                    added.style({backgroundColor: '#C8B560'});
                    gobotany.utils.notify('More filters added'); 
                    gobotany.utils.animate_changed(added);

                    // Load the values for the newly added filters.
                    var watcher = new gobotany.filters.FilterLoadingWatcher(
                        new_filters);
                    watcher.load_values({on_values_loaded: dojo.hitch(
                        this, function() {} ) });

                    this.results_helper.save_filter_state();
                } else {
                    gobotany.utils.notify(
                        'No filters left for the selected character groups');
                }
                button.set('disabled', false);
            })
        });
    },

    _get_filter_display_value: function(value, filter_short_name) {
        var display_value = 'don\'t know';

        if (value !== undefined && value !== '') {
            display_value = value;

            // If the value is numeric, format with correct decimals and unit.
            if (!isNaN(value)) {
                var filter = this.results_helper.filter_manager.get_filter(
                    filter_short_name);
                display_value = gobotany.utils.pretty_length(filter.unit,
                    value);
            }

            // Use special display text for NA values.
            if (value === 'NA') {
                display_value = 'doesn\'t apply';
            }
        }

        return display_value;
    },

    _apply_filter: function(event) {
        dojo.stopEvent(event);

        var choice_div = dojo.query('#' + this.visible_filter_short_name +
                                    ' .choice')[0];

        // First, see if this is a numeric field.

        if (dojo.byId('character_slider') !== null) {
            var char_value_q = dijit.byId('character_slider');
            var value = char_value_q.value;
            if (isNaN(value))
                return;

            this.results_helper.filter_manager.set_selected_value(
                this.visible_filter_short_name, value);
            var display_value = this._get_filter_display_value(value,
                this.visible_filter_short_name);
            choice_div.innerHTML = display_value;
            this.results_helper.save_filter_state();
            this.results_helper.species_section.perform_query();
            this.show_or_hide_filter_clear(
                this.visible_filter_short_name);
            return;
        }

        // Next, look for a traditional checked multiple-choice field.

        var checked_item_q = dojo.query('#character_values_form input:checked');

        if (checked_item_q.length) {
            var checked_item = checked_item_q[0];
            this.results_helper.filter_manager.set_selected_value(
                this.visible_filter_short_name, checked_item.value);
            choice_div.innerHTML =
                this._get_filter_display_value(checked_item.value,
                    this.visible_filter_short_name);
            this.results_helper.species_section.perform_query();
            this.show_or_hide_filter_clear(
                this.visible_filter_short_name);
            return;
        }

        // Well, drat.

        console.log('"Apply" button pressed, but no widget found');
    },

    display_filter: function(filter, idx) {
        var filter_ul = dojo.query('#filters ul')[0];
        var first = null;
        if (idx !== undefined) {
            var nodes = dojo.query('li', filter_ul);
            first = nodes[idx];
            if (first === undefined)
                first = nodes[nodes.length - 1];
        }

        var filterItem = null;
        if (filter.value_type != null) {
            var filterLink = dojo.create('a', {
                href: '#', innerHTML: filter.friendly_name});
            var choiceDiv = dojo.create('div', {
                'class': 'choice',
                innerHTML: this._get_filter_display_value('', '')});
            var removeLink = dojo.create('a', {
                href: '#', innerHTML: '× remove'});
            var clearLink = dojo.create('a', {
                'class': 'clear hidden', href: '#', innerHTML: '× clear'});

            // Pass the filter to the function as its context (this).
            dojo.connect(filterLink, 'onclick', this,
                         function(event) {
                             dojo.stopEvent(event);
                             this.show_filter_working(filter);
                         });
            dojo.connect(removeLink, 'onclick', this,
                         function(event) {
                             dojo.stopEvent(event);
                             this.remove_filter(filter);
                             var current_filter_name = dojo.query(
                                 '#filter-working .name')[0].innerHTML;
                             if (filter.friendly_name ===
                                 current_filter_name) {
                                this.hide_filter_working();
                             }
                         });
            dojo.connect(clearLink, 'onclick', this,
                         function(event) {
                             dojo.stopEvent(event);
                             this.clear_filter(filter);
                         });

            filterItem = dojo.create('li', 
                                     {id: filter.character_short_name});
            dojo.place(filterLink, filterItem);
            dojo.place(choiceDiv, filterItem);
            dojo.place(removeLink, filterItem);
            dojo.place(clearLink, filterItem);

            if (first != null) {
                dojo.place(filterItem, first, 'before');
                dojo.style(filterItem, {backgroundColor: '#C8B560'});
            } else {
                dojo.place(filterItem, filter_ul);
            }

            this.update_filter_display(filter);
        }

        return filterItem;
    },

    show_or_hide_filter_clear: function(filter_character_short_name) {
        // Show or hide the Clear link for a filter at left.
        var filter_id = '#' + filter_character_short_name;
        var should_hide_clear = dojo.query(filter_id +
            ' .choice')[0].innerHTML === 'don\'t know';
        var clear = dojo.query(filter_id + ' .clear');
        if (should_hide_clear) {
            clear.addClass('hidden');
        }
        else {
            clear.removeClass('hidden');
        }
    },

    clear_filters: function() {
        dojo.query('#filters ul').empty();
        this.save_filter_state();
    },

    display_filters: function(filters, idx) {
        var added = dojo.NodeList();
        for (var i = 0; i < filters.length; i++) {
            var f = this.display_filter(filters[i], idx);
            added.push(f);
            if (idx !== undefined)
                idx++;
        }

        return added;
    },

    apply_family_filter: function(event) {
        if (! this.did_they_just_choose_a_genus) {
            dijit.byId('genus_select').set('value', '');
        }

        var family_select = dijit.byId('family_select');
        var family = family_select.value;
        this.set_value('family', family);

        this.results_helper.species_section.perform_query();
        this.did_they_just_choose_a_genus = false;
    },

    apply_genus_filter: function(event) {
        var genus = dijit.byId('genus_select').value;
        this.set_value('genus', genus);

        var family_select = dijit.byId('family_select');
        if (genus) {
            var family = family_select.value;

            var new_family = genus_to_family[genus];
            if (family != new_family) {
                this.did_they_just_choose_a_genus = true;
                this.set_value('family', new_family);
            } else {
                this.results_helper.species_section.perform_query();
            }
        } else {
            this.results_helper.species_section.perform_query();
        }
    },

    clear_family: function(event) {
        dojo.stopEvent(event); 
        this.set_value('family', null);
    },

    clear_genus: function(event) {
        dojo.stopEvent(event);
        this.set_value('genus', null);
    },

    add_callback_filters: function() {
        this.results_helper.filter_manager.add_callback_filter({
            character_short_name: 'family',
            filter_callback: function(filter, item) {
                if (!filter.selected_value)
                    return true;
                return filter.selected_value == item.family;
            }
        });
        this.results_helper.filter_manager.add_callback_filter({
            character_short_name: 'genus',
            filter_callback: function(filter, item) {
                if (!filter.selected_value)
                    return true;
                return filter.selected_value == item.genus;
            }
        });
    },

    set_value: function(char_name, value) {
        this.results_helper.filter_manager.set_selected_value(char_name, value);
        this.update_filter_display(char_name);
    },

    update_filter_display: function(obj) {
        var char_name = null;
        var value = null;

        if (obj.isInstanceOf && obj.isInstanceOf(gobotany.filters.Filter)) {
            value = obj.selected_value;
            char_name = obj.character_short_name;
        } else {
            value = this.results_helper.filter_manager.get_selected_value(obj);
            char_name = obj;
        }

        if (value !== undefined) {
            if (char_name == 'family') {
                dijit.byId('family_select').set('value', value);
            } else if (char_name == 'genus')
                dijit.byId('genus_select').set('value', value);
            else {
                if (value !== null) {
                    var display_value = this._get_filter_display_value(value,
                        char_name);
                    var choice_div = dojo.query('#' + char_name + ' .choice')[0];
                    choice_div.innerHTML = display_value;
                }
                this.show_or_hide_filter_clear(char_name);
            }
        }
    },

    clear_filter: function(filter) {
        if (filter.character_short_name == filter.visible_filter_short_name) {
            this.hide_filter_working();
        }

        if (this.results_helper.filter_manager.get_selected_value(filter.character_short_name)) {
            this.results_helper.filter_manager.set_selected_value(filter.character_short_name, undefined);
            this.results_helper.species_section.perform_query();
        }

        dojo.query('#' + filter.character_short_name + ' .choice'
                  )[0].innerHTML = this._get_filter_display_value('', '');
        this.show_or_hide_filter_clear(filter.character_short_name);
    },

    remove_filter: function(filter) {
        
        if (filter.character_short_name == filter.visible_filter_short_name) {
            this.hide_filter_working();
        }

        if (this.results_helper.filter_manager.has_filter(filter.character_short_name)) {
            this.results_helper.filter_manager.remove_filter(filter.character_short_name);
            this.results_helper.species_section.perform_query();
        }

        dojo.query('#' + filter.character_short_name).orphan();
    },

    hide_filter_working: function() {
        dojo.query('#filter-working').style({display: 'none'});
        this.visible_filter_short_name = null;
    },

    sort_filter_values: function(a, b) {
        // Custom sort for ordering filter values for display.
        var value_a = a.value.toLowerCase();
        var value_b = b.value.toLowerCase();

        // If both values are a number or begin with one, sort numerically.
        var int_value_a = parseInt(value_a);
        var int_value_b = parseInt(value_b);
        if (!isNaN(int_value_a) && !isNaN(int_value_b)) {
            return int_value_a - int_value_b;
        }

        // Otherwise, sort alphabetically.
        // Exception: always make Doesn't Apply (NA) last.
        if (value_a === 'na') {
            return 1;
        }
        if (value_a < value_b) {
            return -1;
        }
        if (value_a > value_b) {
            return 1;
        }

        return 0; // default value (no sort)
    },

    show_filter_working: function(filter) {
        dojo.query('#filter-working').style({display: 'block'});
        dojo.query('#filter-working .name')[0].innerHTML = filter.friendly_name;

        this.visible_filter_short_name = filter.character_short_name;

        var valuesList = dojo.query('#filter-working form .values')[0];
        dojo.empty(valuesList);

        if (filter.values === undefined) {
            console.log(
                'No filter values exist: ' + filter.friendly_name +
                    ' (character_short_name: ' + filter.character_short_name +
                    '  value_type: ' + filter.value_type +
                    '  unit: ' + filter.unit +
                    '  pile_slug: ' + filter.pile_slug + ')');
            return;
        }

        /* Clean up an old ruler before rebuilding the working area. */

        if (this.ruler) {
            this.ruler.destroy();
            dojo.query(this.slider_node).orphan();
            this.ruler = this.slider_node = null;
        }

        /* Build the new DOM elements. */

        if (filter.value_type == 'LENGTH') {
            var unit = filter.unit;

            if (unit === null || unit === undefined) {
                unit = 'mm';
                console.warn('[' + filter.character_short_name +
                    '] Measurement has no unit, defaulting to mm');
            }

            // Create a slider with horizontal rules and labels.

            var themin = filter.values.min;
            var themax = filter.values.max;
            var startvalue = (themax + themin) / 2.0;

            var selectedvalue =
                this.results_helper.filter_manager.get_selected_value(
                    filter.character_short_name);
            if (selectedvalue != null) {
                startvalue = selectedvalue;
            }

            var p = gobotany.utils.pretty_length;
            var pretty1 = p('mm', filter.values.min);
            var pretty2 = p('mm', filter.values.max);
            var label = dojo.place('<label>Select a length between<br>' +
                                   p('mm', filter.values.min) +
                                   ' (' + p('in', filter.values.min) + ')' +
                                   ' and<br>' +
                                   p('mm', filter.values.max) +
                                   ' (' + p('in', filter.values.max) + ')' +
                                   '<br></label>',
                                   valuesList);

            this.slider_node = dojo.create('div', null, valuesList);
            this.ruler = gobotany.sk.RulerSlider(
                this.slider_node, 600, themin, themax, startvalue);

        } else {

            // Create the radio-button widget.

            // Create a Don't Know radio button item.
            var item_html = '<input type="radio" name="char_name" value="" ' +
                       'checked> ' + this._get_filter_display_value('', '');
            var dont_know_item = dojo.create('label',
                                             {'innerHTML': item_html});
            // Connect filter radio button item to a function that will set the
            // Key Characteristics and Notable Exceptions for the filter.
            // Here the *filter* is passed as the context.
            dojo.connect(dont_know_item, 'onclick', this,
                         function(event) {
                             this.update_filter_working_help_text(filter);
                         });
            dojo.place(dont_know_item, valuesList);

            // Apply a custom sort to the filter values.
            var values = gobotany.utils.clone(filter.values);
            values.sort(this.sort_filter_values);

            // Create radio button items for each character value.
            for (var i = 0; i < values.length; i++) {
                var v = values[i];
                
                if ( !((v.count === 0) && (v.value === 'NA')) ) {
                
                    var item_html = '<input type="radio" name="char_name" ' +
                        'value="' + v.value + '"';
                    if (v.count === 0) {
                        item_html = item_html + ' class="zero" disabled';
                    }
                    var display_value =
                        this._get_filter_display_value(v.value,
                            filter.character_short_name);
                    item_html = item_html + '><span> ' + display_value + 
                        '</span> <span>(' + v.count + ')</span>';
                    var character_value_item = dojo.create('label', 
                        {'innerHTML': item_html}, valuesList);
                    this.glossarizer.markup(character_value_item.childNodes[1]);
                    // Connect filter character value radio button item to a function
                    // that will set the Key Characteristics and Notable Exceptions for
                    // filter particular character value. Here the *character value*
                    // is passed as the context.
                    dojo.connect(
                        character_value_item, 'onclick', {helper: this, value: v},
                        function(event) {
                            this.helper.update_filter_working_help_text(this.value);
                        }
                    );
                }
            }

            // If the user has already selected a value for the filter, we
            // pre-check that radio button, instead of pre-checking the
            // first (the "Don't know") radio button like we normally do.

            var selector = '#filter-working .values input';
            var already_selected_value = this.results_helper.filter_manager.get_selected_value(
                filter.character_short_name);
            if (already_selected_value) {
                selector = selector + '[value="' + already_selected_value + '"]';
            }
            dojo.query(selector)[0].checked = true;
        }

        // Set the key characteristics and notable exceptions for the filter
        // (character). (The ones for character values are set elsewhere.)

        var kc = dojo.query('#filter-working .info .key-characteristics')[0];
        kc.innerHTML = filter.key_characteristics;

        var ne = dojo.query('#filter-working .info .notable-exceptions')[0];
        ne.innerHTML = filter.notable_exceptions;
    },

    // Update the filter working area "help text," which consists of the Key
    // Characteristics and Notable Exceptions areas.
    update_filter_working_help_text: function(filter) {
        var kc = dojo.query('#filter-working .info .key-characteristics')[0];
        kc.innerHTML = filter.key_characteristics;

        var ne = dojo.query('#filter-working .info .notable-exceptions')[0];
        ne.innerHTML = filter.notable_exceptions;

        this.glossarizer.markup(kc);
        this.glossarizer.markup(ne);
    }

});

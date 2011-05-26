// UI code for the Simple Key results/filter page.

// Global declaration for JSLint (http://www.jslint.com/)
/*global console, dojo, dojox, dijit, gobotany, document, window,
  _global_setSidebarHeight */

dojo.provide('gobotany.sk.results');

dojo.require('gobotany.sk.RulerSlider');
dojo.require('gobotany.sk.glossary');
dojo.require('gobotany.sk.results.SpeciesSectionHelper');
dojo.require('gobotany.sk.working_area');
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
dojo.require('dijit.form.FilteringSelect');
dojo.require('dijit.form.Form');
dojo.require('dijit.form.HorizontalSlider');
dojo.require('dijit.form.Select');

dojo.declare('gobotany.sk.results.ResultsHelper', null, {
    _loading_filter_count: 2, // 1 for the FilterManager, 1 assuming a filter

    constructor: function(/*String*/ pile_slug) {
        // summary:
        //   Helper class for managing the sections on the results page.
        // description:
        //   Coordinates all of the dynamic logic on the results page.
        //   The procedure for using this class is to instantiate it
        //   and then call its setup() method.
        // | var helper = new gobotany.sk.results.ResultsHelper('some_pile');
        // | helper.setup();

        this.pile_slug = pile_slug;
        this.pile_manager = new gobotany.piles.PileManager(this.pile_slug);
        this.filter_manager = new gobotany.filters.FilterManager({
            pile_slug: this.pile_slug,
            onload: dojo.hitch(this, this.filter_loaded)
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

        this.species_section =
            new gobotany.sk.results.SpeciesSectionHelper(this);
        this.species_section.setup_section();

        this.filter_section =
            new gobotany.sk.results.FilterSectionHelper(this);
        this.filter_section.setup_section();

        // Wire up the filter working area's close button.
        var el = dojo.query('div.working-area .close')[0];
        dojo.connect(el, 'onclick', dojo.hitch(this.filter_section,
            this.filter_section.hide_filter_working));

        dojo.subscribe('results_loaded',
            dojo.hitch(this, this.populate_image_types));

        // Update images on selection change
        var select_box = dijit.byId('image-type-selector');
        dojo.connect(select_box, 'onChange',
                     dojo.hitch(this, this.load_selected_image_type));

        dojo.connect(this.pile_manager, 'on_pile_info_changed', dojo.hitch(
            this, function(pile_info) {

                this.filter_section._setup_character_groups(
                    pile_info.character_groups);

                this.filter_manager.plant_preview_characters =
                    pile_info.plant_preview_characters;

                // A hash means filter state has been set: don't load up the
                // default filters for a pile if filter state has already been
                // set.

                var filters_loaded = dojo.hitch(this, function(filters) {
                    // Note that we increment _loading_filter_count,
                    // because it might be non-zero if the page is still
                    // doing its initial load.
                    this._loading_filter_count += filters.length - 1;
                    console.log('setup: increment _loading_filter_count' +
                        ' to ' + this._loading_filter_count);
                    this._loaded_filters = filters;
                    var filter_loaded = dojo.hitch(this, this.filter_loaded);
                    for (i = 0; i < filters.length; i++) {
                        filters[i].load_values({
                            base_vector: this.filter_manager.base_vector,
                            onload: filter_loaded
                        });
                    }
                });

                if (dojo.hash()) {
                    this.setup_filters_from_hash({
                        on_complete: filters_loaded});
                }
                else {
                    this.setup_filters_from_pile_info({
                        on_complete: filters_loaded});
                }
            })
        );

        this.pile_manager.load();

        // Set up the onhashchange event handler, which will be used to detect
        // Back button undo events for modern browsers.
        dojo.connect(document.body, 'onhashchange', this, this.handle_undo,
                     true);
    },

    // Called each time a filter is finished loading; when the last
    // filter that we are currently waiting for finishes, we kick off
    // some page-update code.
    filter_loaded: function() {
        this._loading_filter_count--;
        console.log('filter_loaded: decrement _loading_filter_count to ' +
                    this._loading_filter_count);
        if (this._loading_filter_count > 0)
            return;  // wait on last filter to be loaded

        console.log('filter_loaded: all filters loaded.');

        // If there's a URL hash, make a call to set up filter values from it
        // again now that all the filters and values have finally loaded; this
        // time omit the onComplete callback.
        if (dojo.hash()) {
            console.log('filter_loaded: about to set up filters from hash');
            this.setup_filters_from_hash();
        }

        console.log('filter_loaded: about to list filters, then run query');
        this.filter_section.display_filters(this._loaded_filters);
        this.filter_section.update_filter_display('family');
        this.filter_section.update_filter_display('genus');

        dojo.query('#sidebar .loading').addClass('hidden');
        this.species_section.perform_query();

        // Show the filter working area if necessary.
        var filter_name = this.filter_section.visible_filter_short_name;
        if (filter_name !== '') {
            var filter = this.filter_manager.get_filter(filter_name);
            if (filter !== undefined) {
                this.filter_section.show_filter_working(filter);
            }
        }
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
        var x;
        for (x = 0; x < pile_info.default_filters.length; x++) {
            var obj = pile_info.default_filters[x];
            obj.pile_slug = this.pile_slug;
            var filter = this.filter_manager.add_filter(
                pile_info.default_filters[x]);
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
        if (hash_object._filters === undefined) {
            return;
        }

        var comma = hash_object._filters.split(',');
        var filter_values = {};
        var filter_names = [];
        var x;
        for (x = 0; x < comma.length; x++) {
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

        // Restore the name of the filter visible in the filter working area,
        // if applicable. It will be shown later when results are loaded.
        if (hash_object._visible !== undefined) {
            this.filter_section.visible_filter_short_name =
                hash_object._visible;
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

        // Save the current state.

        var hash = this.filter_manager.as_query_string();

        // Include a URL parameter indicating whether the filter working area
        // is open.
        if (/&$/.test(hash) === false) {
            hash = hash + '&';
        }
        hash = hash + '_visible=' +
            this.filter_section.visible_filter_short_name;

        // Usually, do not replace the current Back history entry; rather,
        // create a new one, to enable the user to move back and forward
        // through their keying choices.
        var replace_current_history_entry = false;

        // However, upon the initial entry to plant ID keying (where there's
        // no hash yet), do not create a new Back history entry when replacing
        // the hash. This is to help avoid creating a "barrier" when the user
        // tries to navigate back to the pile ID pages using the Back button.
        //console.log('** href: ' + window.location.href);
        //console.log('** hash: ' + window.location.hash);
        if (window.location.hash === '') {   // empty hash: initial page load
            replace_current_history_entry = true;
        }
        //console.log('** replace_current_history_entry: ' +
        //    replace_current_history_entry);

        dojo.hash(hash, replace_current_history_entry);

        dojo.cookie(LAST_URL_COOKIE_NAME, window.location.href, {path: '/'});
    },

    load_selected_image_type: function(event) {
        var image_type = dijit.byId('image-type-selector').value;
        var images = dojo.query('.plant-list img');
        // Replace the image for each plant on the page
        var i;
        for (i = 0; i < images.length; i++) {
            var image = images[i];
            // Fetch the species for the current image
            this.filter_manager.get_species({
                scientific_name: dojo.attr(image, 'x-plant-id'),
                onload: function(item) {
                    // Search for an image of the correct type
                    var new_image;
                    var j;
                    for (j = 0; j < item.images.length; j++) {
                        if (item.images[j].type === image_type) {
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
                        var src_var = dojo.attr(image, 'x-tmp-src') ?
                            'x-tmp-src' : 'src';
                        dojo.attr(image, src_var, new_image.thumb_url);

                        dojo.attr(image, 'alt', new_image.title);
                        // Hide the empty box if it exists and make
                        // sure the image is visible.
                        dojo.query('+ span.MissingImage', image).orphan();
                        dojo.style(image, 'display', 'inline');
                    }
                    else if (dojo.style(image, 'display') !== 'none') {
                        // If there's no matching image display the
                        // empty box and hide the image
                        dojo.style(image, 'display', 'none');
                        dojo.create('span', {'class': 'MissingImage'},
                            image, 'after');
                    }
                }
            });
        }
        this.species_section.lazy_load_images();
    },

    // A subscriber for results_loaded
    populate_image_types: function(message) {
        var results = message.data.items;
        var select_box = dijit.byId('image-type-selector');
        // clear the select
        select_box.options.length = 0;
        // image types depend on the pile, we get the allowed values from
        // the result set for now
        var image_types = [];
        var image_type;
        var i;
        for (i = 0; i < results.length; i++) {
            var images = results[i].images;
            var j;
            for (j = 0; j < images.length; j++) {
                image_type = images[j].type;
                if (image_types.indexOf(image_type) === -1) {
                    image_types.push(image_type);
                }
            }
        }
        // sort lexicographically
        image_types.sort();
        for (i = 0; i < image_types.length; i++) {
            image_type = image_types[i];
            select_box.addOption({value: image_type,
                label: image_type});
            // Habit is selected by default
            if (image_type === 'habit') {
                select_box.attr('value', 'habit');
            }
        }
    }
});


dojo.declare('gobotany.sk.results.FilterSectionHelper', null, {
    ruler: null,
    simple_slider: null,
    slider_node: null,

    constructor: function(results_helper) {
        // summary:
        //   Manages the filters section of the results page (including
        //   the genus/family filters).
        // results_helper:
        //   An instance of gobotany.sk.results.ResultsHelper

        this.results_helper = results_helper;
        this.glossarizer = gobotany.sk.glossary.Glossarizer();

        // This variable is for keeping track of which filter is currently
        // visible in the filter working area (if any).
        this.visible_filter_short_name = '';
    },

    setup_section: function() {
        console.log('FilterSectionHelper: setting up section');

        // Wire up the Get Choices links (a button atop the sidebar and
        // a hyperlink at bottom).
        var choices_button = dojo.query('#sidebar .get-choices')[0];
        dojo.connect(choices_button, 'onclick', this, function(event) {
            dojo.stopEvent(event);
            this.query_best_filters();
        });
        var choices_link = dojo.query('#sidebar .get-more-choices')[0];
        dojo.connect(choices_link, 'onclick', this, function(event) {
            dojo.stopEvent(event);
            this.query_best_filters();
        });

        // Wire up the Apply button in the filter working area.
        var apply_button = dojo.query('.working-area a.apply-btn')[0];
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
        console.log('FilterSectionHelper: Updating character groups');

        var character_groups_list = dojo.query('ul#char-groups')[0];
        dojo.empty(character_groups_list);
        var i;
        for (i = 0; i < character_groups.length; i++) {
            var character_group = character_groups[i];
            var item = dojo.create('li', { innerHTML: '<label>' +
                '<input type="checkbox" value="' + character_group.id +
                '"> ' + character_group.name + '</label>'});
            dojo.place(item, character_groups_list);
        }
    },

    query_best_filters: function() {
        var filter_manager = this.results_helper.filter_manager;
        console.log('FilterSectionHelper: getting more filters...');

        var character_group_ids = [];
        var character_group_items = dojo.query('ul#char-groups input');
        var x;
        for (x = 0; x < character_group_items.length; x++) {
            var item = character_group_items[x];
            if (item.checked) {
                character_group_ids.push(item.value);
            }
        }

        var existing = [];
        for (x = 0; x < filter_manager.filters.length; x++) {
            existing.push(filter_manager.filters[x].character_short_name);
        }
        filter_manager.query_best_filters({
            character_group_ids: character_group_ids,
            existing_characters: existing,
            onLoaded: dojo.hitch(this, function(items) {
                if (items.length > 0) {
                    // Add the new filters to the Filter Manager.
                    var new_filter_names = [];
                    dojo.forEach(items, function(filter_json) {
                        filter_manager.add_filter(filter_json);
                        new_filter_names.push(filter_json.short_name);
                    });

                    // Get all the newly added filters, so they can be
                    // listed on the page and so their values can be loaded.
                    var new_filters = [];
                    var i;
                    for (i = 0; i < new_filter_names.length; i++) {
                        new_filters.push(filter_manager.get_filter(
                            new_filter_names[i]));
                    }

                    // Add the new filters to the filters list.
                    var added = this.display_filters(new_filters, 0);
                    _global_setSidebarHeight();
                    added.style({backgroundColor: '#eeee9a'});
                    gobotany.utils.notify('More choices added');
                    gobotany.utils.animate_changed(added);

                    this.results_helper.save_filter_state();
                }
                else {
                    gobotany.utils.notify(
                        'No more choices left for the boxes checked');
                }
            })
        });
    },

    _get_filter_display_value: function(friendly_text, value,
        filter_short_name) {

        var display_value = 'don\'t know';

        if (value !== undefined && value !== '') {
            display_value = value;

            // If a non-technical label was supplied, use it instead.
            if (friendly_text !== undefined && friendly_text !== '') {
                display_value = friendly_text;
            }

            // If the value is numeric, format with correct decimals and unit.
            // TODO: Unless it's a 'count' filter, in which case don't
            // do anything to the formatting.
            if (!isNaN(value)) {
                var filter = this.results_helper.filter_manager.get_filter(
                    filter_short_name);
                if (filter.is_length()) {
                    display_value = gobotany.utils.pretty_length(filter.unit,
                        value);
                }
                else {
                    display_value = value;
                }
            }

            // Use special display text for NA values.
            if (value === 'NA') {
                display_value = 'doesn\'t apply';
            }
        }

        return display_value;
    },

    _apply_numeric_value: function(choice_div, value) {
        this.results_helper.filter_manager.set_selected_value(
            this.visible_filter_short_name, value);
        var display_value = this._get_filter_display_value('', value,
            this.visible_filter_short_name);
        choice_div.innerHTML = display_value;
        this.results_helper.save_filter_state();
        this.results_helper.species_section.perform_query();
        this.show_or_hide_filter_clear(this.visible_filter_short_name);
    },

    _apply_filter: function(event) {
        dojo.stopEvent(event);

        var value_label = dojo.query('li#' + this.visible_filter_short_name +
            ' span.value')[0];

        // First, see if this is a numeric field.
        var char_value_q;
        var value;
        if (this.ruler !== null) {   // ruler
            value = this.ruler.nearest_legal_value();
            this._apply_numeric_value(value_label, value);
            return;
        } else if (dojo.byId('simple-slider') !== null) {   // count slider
            char_value_q = dijit.byId('simple-slider');
            value = char_value_q.value;
            if (isNaN(value)) {
                return;
            }
            this._apply_numeric_value(value_label, value);
            return;
        }

        // Next, look for a traditional checked multiple-choice field.

        var checked_item_q = dojo.query(
            '#character_values_form input:checked');

        if (checked_item_q.length) {
            value = checked_item_q[0].value;
            this.results_helper.filter_manager.set_selected_value(
                this.visible_filter_short_name, value);
            var filter = this.results_helper.filter_manager.get_filter(
                this.visible_filter_short_name);
            var value_object = filter.choicemap[value];
            var friendly_text = (value_object === undefined ? '' :
                                 value_object.friendly_text);
            value_label.innerHTML = this._get_filter_display_value(
                friendly_text, value, this.visible_filter_short_name);
            this.results_helper.species_section.perform_query();
            this.show_or_hide_filter_clear(
                this.visible_filter_short_name);
            return;
        }

        // Well, drat.

        console.log('"Apply" button pressed, but no widget found');
    },

    display_filter: function(filter, idx) {
        var filter_ul = dojo.query('#sidebar ul.option-list')[0];
        var first = null;
        if (idx !== undefined) {
            var nodes = dojo.query('li', filter_ul);
            if (nodes !== undefined) {
                first = nodes[idx];
                if (first === undefined) {
                    first = nodes[nodes.length - 1];
                }
            }
        }

        var filterItem = null;
        if (filter.value_type !== null) {
            var closeLink = dojo.create('a', {
                href: '#', 'class': 'close'});
            var labelsLink = dojo.create('a', {
                href: '#', 'class': 'option',
                innerHTML: '<span class="name">' + filter.friendly_name +
                    ':</span> <span class="value">' +
                    this._get_filter_display_value('', '', '') + '</span>'});

            var clearLink = dojo.create('a', {
                'class': 'clear hidden', href: '#',
                innerHTML: '<br>× clear'});

            // Pass the filter to the function as its context (this).
            dojo.connect(closeLink, 'onclick', this,
                         function(event) {
                             dojo.stopEvent(event);
                             this.remove_filter(filter);
                             var current_filter_name = '';
                             var working_area_name = dojo.query(
                                 'div.working-area .name');
                             if (working_area_name.length) {
                                 current_filter_name =
                                    working_area_name[0].innerHTML;
                             }
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
            dojo.connect(filterItem, 'onclick', this,
                         function(event) {
                             dojo.stopEvent(event);
                             this.show_filter_working(filter);
                         });

            dojo.place(closeLink, filterItem);
            dojo.place(labelsLink, filterItem);
            dojo.place(clearLink, filterItem);

            if (first !== undefined && first !== null) {
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
        var should_hide_clear = dojo.query('li#' + filter_id +
            ' span.value')[0].innerHTML === 'don\'t know';
        var clear = dojo.query(filter_id + ' .clear');
        if (should_hide_clear) {
            clear.addClass('hidden');
        }
        else {
            clear.removeClass('hidden');
        }
    },

    clear_filters: function() {
        dojo.query('#sidebar ul.option-list').empty();
        this.save_filter_state();
    },

    display_filters: function(filters, idx) {
        var added = dojo.NodeList();
        var i;
        for (i = 0; i < filters.length; i++) {
            var f = this.display_filter(filters[i], idx);
            added.push(f);
            if (idx !== undefined) {
                idx++;
            }
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

            var new_family =
                this.results_helper.species_section.genus_to_family[genus];
            if (family !== new_family) {
                this.did_they_just_choose_a_genus = true;
                this.set_value('family', new_family);
            } else {
                this.results_helper.species_section.perform_query();
            }
        }
        else {
            this.results_helper.species_section.perform_query();
        }
    },

    clear_family: function(event) {
        dojo.stopEvent(event);
        this.set_value('family', null);
        this.set_value('genus', null);
    },

    clear_genus: function(event) {
        dojo.stopEvent(event);
        this.set_value('genus', null);
    },

    set_value: function(char_name, value) {
        this.results_helper.filter_manager.set_selected_value(char_name,
            value);
        this.update_filter_display(char_name);
    },

    update_filter_display: function(obj) {
        var filter = null;
        var char_name = null;
        var value = null;

        if (obj.isInstanceOf && obj.isInstanceOf(gobotany.filters.Filter)) {
            filter = obj;
        }
        else {
            char_name = obj;
            filter = this.results_helper.filter_manager.get_filter(char_name);
        }

        value = filter.selected_value;
        char_name = filter.character_short_name;

        if (value !== undefined) {
            if (char_name === 'family') {
                dijit.byId('family_select').set('value', value);
            }
            else if (char_name === 'genus') {
                dijit.byId('genus_select').set('value', value);
            }
            else {
                if (value !== null) {
                    var value_object = filter.choicemap[value];
                    var friendly_text = (value_object === undefined ? '' :
                                         value_object.friendly_text);
                    var display_value = this._get_filter_display_value(
                        friendly_text, value, char_name);
                    var value_label = dojo.query('li#' + char_name +
                        ' span.value')[0];
                    value_label.innerHTML = display_value;
                }
                this.show_or_hide_filter_clear(char_name);
            }
        }
    },

    clear_filter: function(filter) {
        if (this.results_helper.filter_manager.get_selected_value(
            filter.character_short_name)) {

            this.results_helper.filter_manager.set_selected_value(
                filter.character_short_name, undefined);
            this.results_helper.species_section.perform_query();
        }

        dojo.query('li#' + filter.character_short_name + ' span.value'
                  )[0].innerHTML = this._get_filter_display_value('', '', '');
        this.show_or_hide_filter_clear(filter.character_short_name);
    },

    remove_filter: function(filter) {
        if (filter.character_short_name === this.visible_filter_short_name) {
            this.hide_filter_working();
        }

        if (this.results_helper.filter_manager.has_filter(
            filter.character_short_name)) {

            dojo.query('#' + filter.character_short_name).orphan();
            this.results_helper.filter_manager.remove_filter(
                filter.character_short_name);
            this.results_helper.species_section.perform_query();
        }

        this.results_helper.species_section.lazy_load_images();

        _global_setSidebarHeight();
    },

    hide_filter_working: function() {
        dojo.query('div.working-area').style({display: 'none'});
        this.results_helper.species_section.lazy_load_images();

        // Save the state, which includes whether the filter working area is
        // being shown.
        this.results_helper.save_filter_state();
    },

    set_simple_slider_value: function() {
        var count_display =
            dojo.query('div.working-area #simple-slider .count')[0];
        count_display.innerHTML = this.simple_slider.value;
        var handle = dojo.query('.dijitSliderImageHandleH')[0];
        var pos = dojo.position(handle, true);
        count_display.style.top = (pos.y - 20) + 'px';
        count_display.style.left = pos.x + 'px';
    },

    show_filter_working: function(filter) {
        filter.load_values({
            base_vector: this.results_helper.filter_manager.base_vector,
            onload: dojo.hitch(this, 'show_filter_working_onload')
        });
    },

    clean_up_old_slider: function() {
        // Clean up an old ruler or simple slider before rebuilding the
        // working area.
        if (this.ruler !== null) {
            this.ruler.destroy();
            dojo.query(this.slider_node).orphan();
            this.ruler = this.slider_node = null;
        }
        if (this.simple_slider) {
            this.simple_slider.destroy();
            dojo.query(this.slider_node).orphan();
            this.simple_slider = this.slider_node = null;
        }
    },

    show_ruler_slider: function(filter, values_list) {
        var unit = filter.unit;
        if (unit === null || unit === undefined) {
            unit = 'mm';
            console.warn('[' + filter.character_short_name +
                '] Measurement has no unit, assuming mm');
        }

        // Create a slider with horizontal rules and labels.

        var themin = filter.min;
        var themax = filter.max;
        var startvalue = (themax + themin) / 2.0;
        var selectedvalue =
            this.results_helper.filter_manager.get_selected_value(
                filter.character_short_name);
        if (selectedvalue !== undefined && selectedvalue !== null) {
            startvalue = selectedvalue;
        }

        var p = gobotany.utils.pretty_length;
        dojo.place('<label>Select a length between<br>' +
                   p('mm', themin) +
                   ' (' + p('in', themin) + ') and<br>' +
                   p('mm', themax) +
                   ' (' + p('in', themax) + ')<br></label>',
                   values_list);

        var filter_manager = this.results_helper.filter_manager;
        var vector = filter_manager.compute_species_without(
            filter.character_short_name);
        var ranges = filter.allowed_ranges(vector);
        var rmin = ranges[0].min;
        var rmax = ranges[ranges.length - 1].max;

        var illegal_regions = [];

        if (rmin > 0) illegal_regions.push([- 2 * rmin, rmin]);
        if (rmax < themax) illegal_regions.push([rmax, themax * 2]);

        for (i = 0; i < ranges.length - 1; i++)
            illegal_regions.push([ranges[i].max, ranges[i + 1].min]);

        this.slider_node = dojo.create('div', null, values_list);
        this.ruler = gobotany.sk.RulerSlider(
            this.slider_node, 'character_slider', 600, themax,
            startvalue, illegal_regions);
    },

    show_slider: function(filter, values_list) {
        var num_values = filter.max - filter.min + 1;
        var startvalue = Math.ceil(num_values / 2);
        var selectedvalue =
            this.results_helper.filter_manager.get_selected_value(
                filter.character_short_name);
        if (selectedvalue !== undefined && selectedvalue !== null) {
            startvalue = selectedvalue;
        }
        dojo.place('<label>Select a number between<br>' +
                   filter.min + ' and ' +
                   filter.max + '</label>', values_list);
        this.slider_node = dojo.create('div', null, values_list);
        this.simple_slider = new dijit.form.HorizontalSlider({
            id: 'simple-slider',
            name: 'simple-slider',
            value: startvalue,
            minimum: filter.min,
            maximum: filter.max,
            discreteValues: num_values,
            intermediateChanges: true,
            showButtons: false,
            onChange: dojo.hitch(this, this.set_simple_slider_value),
            onMouseUp: dojo.hitch(this, this.set_simple_slider_value)
            }, this.slider_node);
        dojo.create('div', {
            'class': 'count',
            'innerHTML': startvalue
            }, this.simple_slider.containerNode);
        this.set_simple_slider_value();
    },

    /* A filter object has been returned from Ajax!  We can now set up
       the working area and save the new page state. */

    show_filter_working_onload: function(filter) {
        var C = gobotany.sk.working_area.select_working_area(filter);
        var species_vector = this.results_helper.filter_manager.
            compute_species_without(filter.character_short_name);
        this.working_area = C(dojo.query('div.working-area'), filter,
                              species_vector, this.glossarizer, null);

        // Save the state, which includes whether the filter working area is
        // being shown.
        this.visible_filter_short_name = filter.character_short_name;
        this.results_helper.save_filter_state();

        _global_setSidebarHeight();
    }

});

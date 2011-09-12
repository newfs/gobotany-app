// UI code for the Simple Key results/filter page.

// Global declaration for JSLint (http://www.jslint.com/)
/*global console, dojo, dojox, dijit, gobotany, document, window,
  global_setSidebarHeight */

dojo.provide('gobotany.sk.results');

dojo.require('gobotany.sk.RulerSlider');
dojo.require('gobotany.sk.glossary');
dojo.require('gobotany.sk.SpeciesSectionHelper');
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
    _loading_filter_count: 2, // assume at least the FilterManager + 1 filter

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

        // Whenever a new filter value on the page is applied, the
        // filter manager should re-run its query and notify everyone.
        dojo.subscribe('/sk/filter/change', this.filter_manager,
                       'perform_query');
   },

    setup: function() {
        // summary:
        //   Sets up the results page with appropriate callbacks
        // description:
        //   Connects callback functionality and generally sets up
        //   the logic of the page ready for use, this should only
        //   be called once.

        console.log('ResultsHelper: setting up page - ' + this.pile_slug);

        this.family_genus_selectors =
            gobotany.sk.results.FamilyGenusSelectors({
                filter_manager: this.filter_manager
            });

        this.species_section =
            new gobotany.sk.SpeciesSectionHelper(this);
        this.species_section.setup_section();

        new gobotany.sk.SpeciesCounts(this);

        this.filter_section =
            new gobotany.sk.results.FilterSectionHelper(this);
        this.filter_section.setup_section();

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

                this.species_section.plant_preview_characters =
                    pile_info.plant_preview_characters;

                // Set up a callback function that will be called once
                // the filters are set up.

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

                // Set up the filters from URL hash values if the list of
                // filters is present in the hash. Otherwise, set up the
                // default filters from the pile info, and if just a family
                // or genus was passed (examples: /#family=... /#genus=...),
                // those values will be set later.

                var should_set_up_from_hash = false;
                var hash_value = dojo.hash();
                if (hash_value !== undefined) {
                    var hash_object = dojo.queryToObject(hash_value);
                    if (hash_object._filters) {  // hash parameter '_filters'
                        should_set_up_from_hash = true;
                    }
                }
                console.log('should_set_up_from_hash = ' +
                    should_set_up_from_hash);

                if (should_set_up_from_hash) {
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
    filter_loaded: function(filter) {
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
        
        // Re-initialize the scroll pane now that its contents have changed.
        this.filter_section.scroll_pane_api.reinitialise();
        
        this.filter_section.update_filter_display('family');
        this.filter_section.update_filter_display('genus');

        dojo.query('#sidebar .loading').addClass('hidden');

        dojo.publish('/sk/filter/change', [filter]);

        // Show a filter in the filter working area if necessary.
        var filter_name = this.filter_section.visible_filter_short_name;
        if (filter_name !== '') {
            var filter = this.filter_manager.get_filter(filter_name);
            if (filter !== undefined)
                this.filter_section.show_filter_working(filter);
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
        console.log('hash_object:');
        console.log(hash_object);

        var filter_values = {};
        var filter_names = [];
        if (hash_object._filters !== undefined) {
            var comma = hash_object._filters.split(',');
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
        }

        // Handle family or genus filter values, if applicable.
        if (hash_object.family) {
            this.filter_manager.set_selected_value('family',
                hash_object.family);
            dojo.publish('/sk/filter/change',
                [this.family_genus_selectors.family_filter]);
        }
        if (hash_object.genus) {
            this.filter_manager.set_selected_value('genus',
                hash_object.genus);
            dojo.publish('/sk/filter/change',
                [this.family_genus_selectors.genus_filter]);
        }

        // Restore the filter that was last visible in the filter working
        // area, if applicable. It will be shown later when results load.
        if (hash_object._visible !== undefined) {
            this.filter_section.visible_filter_short_name =
                hash_object._visible;
        }

        if (filter_names.length > 0) {
            console.log('setup_filters_from_hash: about to call ' +
                'filter_manager.query_filters with filter_names: ' +
                filter_names);
            this.filter_manager.query_filters({
                short_names: filter_names,
                onLoaded: dojo.hitch(this, function(items) {
                    var filters = [];
                    dojo.forEach(items, dojo.hitch(this, function(item) {
                        var filter_args = gobotany.utils.clone(item,
                            {pile_slug: this.pile_slug});
                        var filter = this.filter_manager.add_filter(
                            filter_args);
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
        }
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
            hash += '&';
        }
        hash += '_visible=' + this.filter_section.visible_filter_short_name;
        
        // Include a URL parameter indicating the current view of the
        // results area.
        if (/&$/.test(hash) === false) {
            hash += '&';
        }
        hash += '_view=' + this.species_section.current_view;

        // Include a URL parameter indicating the current type of photos
        // to show for the photos view.
        if (/&$/.test(hash) === false) {
            hash += '&';
        }
        hash += '_show=' + dijit.byId('image-type-selector').value;

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
        this.save_filter_state();
    },

    // A subscriber for results_loaded
    populate_image_types: function(message) {
        var results = message.query_results;
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
            if (image_type === 'habit')
                select_box.set('value', 'habit');
        }

        // Set the last shown image type if possible.
        var hash_object = dojo.queryToObject(dojo.hash());
        if (hash_object._show !== undefined &&
            hash_object._show && hash_object._show !== '') {

            // Only set the image type if it's a currently valid one.
            var types_regex = RegExp('^(' + image_types.join('|') + ')$');
            if (types_regex.test(hash_object._show)) {
                dijit.byId('image-type-selector').attr('value',
                    hash_object._show);
            }
        }
    }
});


/*
 * Events:
 *
 * '/sk/filter/change' is produced when the user interacts with one of
 * our select boxes to choose a new family or genus from the dropdown
 * (or, conversely, when they clear one of the select widgets).
 *
 * '/sk/filter/change' is consumed and induces us to re-compute the set
 * of valid family and genus values in our select boxes, based on the
 * species that remain.
 */
dojo.declare('gobotany.sk.results.FamilyGenusSelectors', null, {
    constructor: function(args) {
        this.filter_manager = args.filter_manager;

        this.family_store = new dojo.data.ItemFileWriteStore({
            data: {label: 'name', identifier: 'name', items: []}
        });
        this.genus_store = new dojo.data.ItemFileWriteStore({
            data: {label: 'name', identifier: 'name', items: []}
        });
        var family_select = dijit.byId('family_select');
        family_select.set('required', false);
        family_select.set('store', this.family_store);

        var genus_select = dijit.byId('genus_select');
        genus_select.set('required', false);
        genus_select.set('store', this.genus_store);

        dojo.connect(family_select, 'onChange', this, '_on_family_change');
        dojo.connect(genus_select, 'onChange', this, '_on_genus_change');

        // Wire up the "Clear" buttons for the family and genus.
        dojo.connect(dijit.byId('clear_family'), 'onClick', function(event) {
            dojo.stopEvent(event);
            family_select.set('value', '');
        });
        dojo.connect(dijit.byId('clear_genus'), 'onClick', function(event) {
            dojo.stopEvent(event);
            genus_select.set('value', '');
        });

        // Save objects that our callbacks will need.
        this.family_select = family_select;
        this.genus_select = genus_select;

        this.family_filter = this.filter_manager.get_filter('family');
        this.genus_filter = this.filter_manager.get_filter('genus');

        // React when filters change anywhere on the page.
        dojo.subscribe('/sk/filter/change', this, '_on_filter_change');
    },

    /*
     * A filter somewhere else on the page has changed value, so we need
     * to rebuild the family and genus selectors to include only "safe"
     * values that will not result in 0 search results.
     */
    _on_filter_change: function() {
        this._rebuild_selector(this.family_store, this.family_filter);
        this._rebuild_selector(this.genus_store, this.genus_filter);
    },

    _rebuild_selector: function(store, filter) {
        var vector = this.filter_manager.compute_species_without(
            filter.short_name);
        var choices = filter.safe_choices(vector);

        // We cannot control the order of terms in the selector without
        // deleting them all and starting over from the beginning.
        store.fetch({onItem: dojo.hitch(store, 'deleteItem')});
        store.save();
        for (var i = 0; i < choices.length; i++)
            store.newItem({ name: choices[i] });
        store.save();
    },

    /*
     * One of our own select boxes has changed value, so we broadcast
     * that fact to all of the other parts of the page.
     */
    _on_family_change: function(event) {
        this.filter_manager.set_selected_value(
            'family', this.family_select.value);
        dojo.publish('/sk/filter/change', [this.family_filter]);
    },
    _on_genus_change: function(event) {
        this.filter_manager.set_selected_value(
            'genus', this.genus_select.value);
        dojo.publish('/sk/filter/change', [this.genus_filter]);
    }
});


dojo.declare('gobotany.sk.results.FilterSectionHelper', null, {
    ruler: null,
    simple_slider: null,
    slider_node: null,
    scroll_pane: null,
    scroll_pane_api: null,

    constructor: function(results_helper) {
        // summary:
        //   Manages the filters section of the results page (including
        //   the genus/family filters).
        // results_helper:
        //   An instance of gobotany.sk.results.ResultsHelper

        this.results_helper = results_helper;
        this.glossarizer = gobotany.sk.glossary.Glossarizer();
        this.working_area = null;

        // This variable is for keeping track of which filter is currently
        // visible in the filter working area (if any).
        this.visible_filter_short_name = '';
    },

    setup_section: function() {
        console.log('FilterSectionHelper: setting up section');

        // Set up the jQuery scrolling box for filters.
        this.scroll_pane = $('.scroll').jScrollPane({
			                   verticalGutter: 0,
			                   showArrows: true
		                   });
        this.scroll_pane_api = this.scroll_pane.data('jsp');

        // Wire up the Get More Choices link.
        var get_more_choices = dojo.query('#sidebar .get-more a')[0];
        dojo.connect(get_more_choices, 'onclick', this, function() {
            var content_element = dojo.query('#modal')[0];
            Shadowbox.open({
                content: content_element.innerHTML,
                player: 'html',
                height: 450,
                options: {onFinish: function() {
                    // Wire up "Get more choices" button now that it exists.
                    var button = dojo.query('#sb-container a.get-choices');
                    button.onclick(function() {
                        helper.filter_section.query_best_filters();
                        Shadowbox.close();
                    });
                    button.addClass('get-choices-ready');  // for tests
                }}
            });
        });

        // Wire up the Clear All button.
        var clear_all_button = dojo.query('#sidebar a.clear-all-btn')[0];
        dojo.connect(clear_all_button, 'onclick', this,
            this.clear_all_filter_choices);

        // Respond to filter value changes.
        dojo.subscribe('/sk/filter/change', this, '_on_filter_change');
    },

    _setup_character_groups: function(character_groups) {
        console.log('FilterSectionHelper: Updating character groups');

        var character_groups_list = dojo.query('ul.char-groups')[0];
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
        // Get the character group checkbox items that are currently in
        // the Shadowbox modal dialog. These are a copy of the contents
        // of our static HTML div with id "modal" and only exist as long
        // as the Shadowbox dialog is visible.
        var character_group_items =
            dojo.query('#sb-container ul.char-groups input');
        var x;
        for (x = 0; x < character_group_items.length; x++) {
            var item = character_group_items[x];
            if (item.checked) {
                character_group_ids.push(item.value);
            }
        }
        console.log('character_group_items:');
        console.log(character_group_items);
        console.log('checked character_group_ids:');
        console.log(character_group_ids);

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
                    global_setSidebarHeight();
                    added.style({backgroundColor: '#eeee9a'});
                    gobotany.utils.notify('More choices added');
                    gobotany.utils.animate_changed(added);

                    // Re-initialize the scroll pane now that its
                    // contents have changed, and move the scroll bar to
                    // the top so that they can see their new choices.
                    this.scroll_pane_api.reinitialise();
                    this.scroll_pane_api.scrollTo(0, 0);

                    this.results_helper.save_filter_state();
                }
                else {
                    gobotany.utils.notify(
                        'No more choices left for the boxes checked');
                }
            })
        });
    },

    _get_filter_display_value: function(filter) {
        var value = filter.selected_value;

        if (value === null)
            return "don't know";

        if (value === 'NA')
            return "doesn't apply";

        if (filter.value_type === 'TEXT') {
            var choice = filter.choicemap[value];
            return choice.friendly_text || value;
        }

        if (filter.is_length()) {
            var units = filter.display_units || 'mm';
            return gobotany.utils.pretty_length(units, value);
        }

        return value + '';
    },

    display_filter: function(filter, pos) {

        if (filter.value_type === null)
            return null;

        var filter_ul = dojo.query('#sidebar ul.option-list')[0];
        var filter_li = dojo.create('li', {id: filter.character_short_name},
                                    filter_ul, pos);
        var labelsLink = dojo.create('a', {
            href: '#', 'class': 'option',
            innerHTML: '<span class="name">' + filter.friendly_name +
                ':</span> <span class="value">' +
                this._get_filter_display_value(filter) + '</span>'
        }, filter_li);
        var clearLink = dojo.create('a', {
            'class': 'clear-filter', href: '#',
            innerHTML: 'Clear'
        }, filter_li);

        this.glossarizer.markup(labelsLink);

        // Event handling

        dojo.connect(clearLink, 'onclick', this, function(event) {
            dojo.stopEvent(event);
            this.clear_filter(filter);
        });
        dojo.connect(filter_li, 'onclick', this, function(event) {
            dojo.stopEvent(event);
            this.show_filter_working(filter);

            // Set the just-selected filter as active at left.
            dojo.query('.option-list li').removeClass('active');
            dojo.addClass(filter_li, 'active');
        });

        if (typeof(pos) === 'number')
            dojo.style(filter_li, {backgroundColor: '#C8B560'});

        this.update_filter_display(filter);
        return filter_li;
    },

    show_or_hide_filter_clear: function(filter) {
        // Show or hide the Clear link for a filter at left.
        var name = filter.character_short_name;
        var div = dojo.query('#' + name + ' .clear-filter');
        var display_value = 'block';
        if (filter.selected_value === null) {
            display_value = 'none';
        }
        div.style('display', display_value);

        // Re-initialize the scroll pane now that its contents have changed.
        this.scroll_pane_api.reinitialise();
    },

    clear_filters: function() {
        dojo.query('#sidebar ul.option-list').empty();
        this.save_filter_state();
    },

    display_filters: function(filters, pos) {
        var added = dojo.NodeList();
        var i;
        for (i = 0; i < filters.length; i++) {
            var f = this.display_filter(filters[i], pos);
            added.push(f);
            if (typeof(pos) === 'number')  // place at successive positions
                pos++;
        }
        return added;
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
                    var display_value = this._get_filter_display_value(filter);
                    var q = dojo.query('li#' + char_name + ' span.value');
                    q.html(display_value);
                    this.glossarizer.markup(q[0]);
                }
                this.show_or_hide_filter_clear(filter);
            }
        }
    },

    clear_filter: function(filter) {
        if (this.results_helper.filter_manager.get_selected_value(
            filter.character_short_name)) {

            this.results_helper.filter_manager.set_selected_value(
                filter.character_short_name, undefined);
        }

        if (this.working_area !== null)
            if (this.working_area.filter === filter)
                this.working_area.clear();

        dojo.publish('/sk/filter/change', [filter]);

        dojo.query('li#' + filter.character_short_name + ' span.value'
                  ).html(this._get_filter_display_value(filter));
        this.show_or_hide_filter_clear(filter);
    },

    clear_all_filter_choices: function() {
        var filters = this.results_helper._loaded_filters;
        for (var i = 0; i < filters.length; i++) {
            this.clear_filter(filters[i]);
        }
    },

    show_filter_working: function(filter) {
        filter.load_values({
            base_vector: this.results_helper.filter_manager.base_vector,
            onload: dojo.hitch(this, 'show_filter_working_onload')
        });
    },

    /* A filter object has been returned from Ajax!  We can now set up
       the working area and save the new page state. */

    show_filter_working_onload: function(filter) {
        // Dismiss old working area, to avoid having an Apply button
        // that is wired up to two different filters!
        if (this.working_area !== null)
            this.working_area.dismiss();

        var C = gobotany.sk.working_area.select_working_area(filter);

        this.working_area = C({
            div: dojo.query('div.working-area')[0],
            filter: filter,
            filter_manager: this.results_helper.filter_manager,
            glossarizer: this.glossarizer,
            on_dismiss: dojo.hitch(this, 'on_working_area_dismiss')
        });

        // Save the state, which includes whether the filter working area is
        // being shown.
        this.visible_filter_short_name = filter.character_short_name;
        this.results_helper.save_filter_state();

        global_setSidebarHeight();
    },

    /* When the working area is dismissed, we clean up and save state. */

    on_working_area_dismiss: function(filter) {
        this.working_area = null;
        this.results_helper.species_section.lazy_load_images();
        this.visible_filter_short_name = '';
        this.results_helper.save_filter_state();
    },

    /* When the filter value is changed in the working area, we respond. */

    _on_filter_change: function(filter) {
        dojo.query('li#' + filter.character_short_name + ' span.value'
                  ).html(this._get_filter_display_value(filter));
        this.show_or_hide_filter_clear(filter);
    }
});

// UI code for the Simple Key results/filter page.

dojo.provide('gobotany.sk.results');

dojo.require('gobotany.sk.glossary');
dojo.require('gobotany.sk.SpeciesSectionHelper');
dojo.require('gobotany.sk.working_area');
dojo.require('gobotany.filters');
dojo.require('gobotany.utils');

dojo.require('dojo.cookie');
dojo.require('dojo.hash');
dojo.require('dojo.html');
dojo.require('dojo.data.ItemFileWriteStore');
dojo.require('dijit.form.Button');
dojo.require('dijit.form.FilteringSelect');
dojo.require('dijit.form.Select');

dojo.declare('gobotany.sk.results.ResultsHelper', null, {

    constructor: function(/*String*/ pile_slug) {
        // summary:
        //   Helper class for managing the sections on the results page.
        // description:
        //   Coordinates all of the dynamic logic on the results page.

        this.pile_slug = pile_slug;

        this.filter_manager = new gobotany.filters.FilterManager({
            pile_slug: this.pile_slug
        });

        this.species_section =
            new gobotany.sk.SpeciesSectionHelper(this);

        new gobotany.sk.SpeciesCounts(this);

        this.filter_section =
            new gobotany.sk.results.FilterSectionHelper(this);

        dojo.subscribe('results_loaded',
            dojo.hitch(this, this.populate_image_types));

        // Update images on selection change
        App3.addObserver('image_type',
                         $.proxy(this, 'load_selected_image_type'));

        simplekey_resources.pile(this.pile_slug).done(
            dojo.hitch(this, function(pile_info) {

                this.filter_section._setup_character_groups(
                    pile_info.character_groups);

                this.species_section.plant_preview_characters =
                    pile_info.plant_preview_characters;

                // Set up the filters from URL hash values if the list of
                // filters is present in the hash. Otherwise, set up the
                // default filters from the pile info, and if just a family
                // or genus was passed (examples: /#family=... /#genus=...),
                // those values will be set later.

                /* TODO: remove soon */
                /*
                var should_set_up_from_hash = false;
                var hash_value = dojo.hash();
                if (hash_value !== undefined) {
                    var hash_object = dojo.queryToObject(hash_value);
                    if (hash_object._filters) {  // hash parameter '_filters'
                        should_set_up_from_hash = true;
                    }
                }

                if (should_set_up_from_hash) {
                    this.setup_filters_from_hash({
                        on_complete: filters_loaded});
                }
                else {
                    this.setup_filters_from_pile_info({
                        pile_info: pile_info,
                        on_complete: filters_loaded});
                }
                */
            }));

        // Set up the onhashchange event handler, which will be used to detect
        // Back button undo events for modern browsers.
        dojo.connect(document.body, 'onhashchange', this, this.handle_undo,
                     true);

        // Set up a handler to detect an Esc keypress, which will close
        // the filter working area if it is open.
        dojo.connect(document.body, 'onkeypress',
            dojo.hitch(this, this.handle_keys));
    },

    handle_keys: function(e) {
        switch (e.charOrCode) {
            case dojo.keys.ESCAPE:
                if (this.filter_section.working_area) {
                    this.filter_section.working_area.dismiss();
                }
                break;
        }
    },

    // Called when all filters are loaded and the species list has been
    // received and processed by the filter manager.
    finish_initialization: function(filter) {

        return;

        // TODO: John will pop up the working area based on URL, like this did:

        // Show a filter in the filter working area if necessary.
        // var filter_name = this.filter_section.visible_filter_short_name;
        // if (filter_name !== '') {
        //     var filter = this.filter_manager.get_filter(filter_name);
        //     if (filter !== undefined)
        //         this.filter_section.show_filter_working(filter);
        // }
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

    /* TODO: remove soon */
    /*
    setup_filters_from_pile_info: function(args) {
        // summary:
        //   Sets up the internal filter data structure based on default
        //   filters in the pile info.

        var default_filters = args.pile_info.default_filters;
        var filters = [];
        for (var i = 0; i < default_filters.length; i++) {
            var filter = this.filter_manager.add_filter(default_filters[i]);
            filters.push(filter);
        }
        if (args && args.on_complete)
            args.on_complete(filters);
    },
    */

    /* TODO: remove soon */
    /*
    setup_filters_from_hash: function(args) {
        // summary:
        //   Sets up the internal filter data structure based on values in
        //   in the url hash (dojo.hash())

        console.log('setting up from hash - ' + dojo.hash());

        var hash_object = dojo.queryToObject(dojo.hash());
        // console.log('hash_object:');
        // console.log(hash_object);

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
            simplekey_resources.pile_characters(this.pile_slug)
                .done(dojo.hitch(this, function(items) {
                    var filters = [];
                    dojo.forEach(items, dojo.hitch(this, function(item) {
                        if (_.indexOf(filter_names, item.short_name) == -1)
                            // Because all filters come back, we have to
                            // skip the ones we do not want.
                            return;
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
                }));
        }
    },
    */

    save_filter_state: function() {

        return; // TODO: John will make this part of his ResultsPageState

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
        if (App3.image_type)
            hash += '_show=' + App3.image_type;

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
        var image_type = App3.image_type;
        if (!image_type)
            return;

        var image_tags = dojo.query('.plant-list img');
        // Replace the image for each plant on the page
        var i;
        for (i = 0; i < image_tags.length; i++) {
            var image_tag = image_tags[i];

            // See if the taxon has an image for the new image type.
            var scientific_name = dojo.attr(image_tag, 'x-plant-id');
            taxon = App3.taxa_by_sciname[scientific_name];
            var new_image = _.find(taxon.images, function(image) {
                return image.type === image_type});

            if (new_image) {
                dojo.attr(image_tag, 'x-tmp-src', new_image.thumb_url);
                dojo.attr(image_tag, 'alt', new_image.title);
                // Hide the empty box if it exists and make
                // sure the image is visible.
                dojo.query('+ div.missing-image', image_tag).orphan();
                dojo.style(image_tag, 'display', 'inline');

            } else if (dojo.style(image_tag, 'display') !== 'none') {
                // If there's no matching image display the
                // empty box and hide the image
                dojo.style(image_tag, 'display', 'none');
                dojo.create('div', {
                    'class': 'missing-image',
                    'innerHTML': '<p>Image not available yet</p>'
                }, image_tag, 'after');
            }
        }
        this.species_section.lazy_load_images();
        this.save_filter_state();
    },

    // A subscriber for results_loaded
    populate_image_types: function(message) {
        // Get an object that tells which image type should be the
        // default selected menu item, and any image types to omit.
        var menu_config = results_photo_menu[this.pile_slug];
        var results = message.query_results;

        var image_list = _.flatten(_.pluck(results, 'images'));
        var all_image_types = _.uniq(_.pluck(image_list, 'type'));
        var image_types = _.difference(all_image_types, menu_config['omit']);

        // Add image types to the <select> and set the default value.
        image_types.sort();
        App3.image_types.set('content', image_types);

        var default_type = menu_config['default'];
        if (image_types.indexOf(default_type) === -1)
            var default_type = image_types[0];
        App3.set('image_type', default_type);
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
        this.working_area = null;

        // This variable is for keeping track of which filter is currently
        // visible in the filter working area (if any).
        this.visible_filter_short_name = '';
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

    //        this.glossarizer.markup(labelsLink);
    // if (typeof(pos) === 'number')
    //     dojo.style(filter_li, {backgroundColor: '#c8b560'});
    // gobotany.utils.animate_changed(dojo.query(q), {'end_color': '#ffd'});

    /* A filter object has been returned from Ajax!  We can now set up
       the working area and save the new page state. */

    show_filter_working_onload: function(filter, y) {
        // Dismiss old working area, to avoid having an Apply button
        // that is wired up to two different filters!
        if (this.working_area !== null)
            this.working_area.dismiss();

        var C = gobotany.sk.working_area.select_working_area(filter);

        this.working_area = C({
            div: $('div.working-area')[0],
            filter: filter,
            y: y,
            glossarizer: this.glossarizer,
            on_dismiss: dojo.hitch(this, 'on_working_area_dismiss')
        });

        // Save the state, which includes whether the filter working area is
        // being shown.
        this.visible_filter_short_name = filter.character_short_name;
        this.results_helper.save_filter_state();

        sidebar_set_height();
    },

    /* When the working area is dismissed, we clean up and save state. */

    on_working_area_dismiss: function(filter) {
        this.working_area = null;
        this.visible_filter_short_name = '';
        this.results_helper.save_filter_state();

        // Clear selected state in the questions list at left.
        $('.option-list li').removeClass('active');
    }
});



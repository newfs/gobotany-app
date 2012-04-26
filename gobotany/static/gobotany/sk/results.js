// UI code for the Simple Key results/filter page.

dojo.provide('gobotany.sk.results');

dojo.require('gobotany.sk.glossary');
dojo.require('gobotany.sk.SpeciesSectionHelper');
dojo.require('gobotany.sk.working_area');
dojo.require('gobotany.utils');

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
            }));

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

        sidebar_set_height();
    },

    /* When the working area is dismissed, we clean up and save state. */

    on_working_area_dismiss: function(filter) {
        this.working_area = null;
        this.visible_filter_short_name = '';

        // Clear selected state in the questions list at left.
        $('.option-list li').removeClass('active');
    }
});



// UI code for the Simple Key results/filter page.

dojo.provide('gobotany.sk.results');

dojo.require('gobotany.sk.SpeciesSectionHelper');
dojo.require('gobotany.sk.working_area');

var results_photo_menu = dojo.require('simplekey/results_photo_menu');

dojo.declare('gobotany.sk.results.ResultsHelper', null, {

    constructor: function(/*String*/ pile_slug) {
        // summary:
        //   Helper class for managing the sections on the results page.
        // description:
        //   Coordinates all of the dynamic logic on the results page.

        this.pile_slug = pile_slug;

        this.species_section =
            new gobotany.sk.SpeciesSectionHelper(pile_slug);

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

    load_selected_image_type: function(event) {
        var image_type = App3.image_type;
        if (!image_type) {
            // No image types available yet, so skip for now
            return;
        }

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

        if (_.isEqual(App3.image_types.get('content'), image_types))
            // Avoid generating events when nothing has changed.
            return;

        App3.image_types.set('content', image_types);

        var old = App3.get('image_type');
        if (typeof old === 'undefined' || image_types.indexOf(old) === -1) {
            var default_type = menu_config['default'];
            if (image_types.indexOf(default_type) === -1)
                default_type = image_types[0];
            App3.set('image_type', default_type);
        }

        // Load the images.
        this.load_selected_image_type();
    }
});


dojo.declare('gobotany.sk.results.FilterSectionHelper', null, {
    working_area: null,

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
            on_dismiss: dojo.hitch(this, 'on_working_area_dismiss')
        });

        sidebar_set_height();
    },

    /* When the working area is dismissed, we clean up and save state. */

    on_working_area_dismiss: function(filter) {
        this.working_area = null;

        // Clear selected state in the questions list at left.
        $('.option-list li').removeClass('active');
    }
});

define([
    'bridge/jquery',
    'bridge/shadowbox',
    'bridge/underscore',
    'plantpreview/popup',
    'simplekey/App3',
    'simplekey/results_photo_menu',
    'simplekey/utils',
    'util/glossarizer',
    'util/lazy_images'
], function($, Shadowbox, _, plantpreview_popup,
            App3, results_photo_menu, utils,
            glossarizer, lazy_images) {

    var SpeciesSection = function() {};
    var glossarize = glossarizer.glossarize;
    var methods = SpeciesSection.prototype = {};

    methods.init = function(pile_slug, taxa_ready, plant_divs_ready) {
        // summary:
        //   Manages the species section of the results page

        this.pile_slug = pile_slug;
        this.plant_list = $('#main .plant-list');
        this.plant_data = [];
        this.plant_divs = [];
        this.plant_divs_ready = plant_divs_ready;

        taxa_ready.done(
            $.proxy(this, 'create_plant_divs')
        );
    };

    methods.default_image = function(species) {
        for (var i = 0; i < species.images.length; i += 1) {
            var image = species.images[i];
            if (image.rank === 1 && image.type === 'habit')
                return image;
        }
        return {};
    };

    methods.get_number_of_rows_to_span = function(items, start) {
        /* From a starting point in a list of plant items, return the number
           of rows it takes to get to the next genus (or the end of the
           list). */

        var rows = 1;
        var i;
        for (i = start; i < items.length; i += 1) {
            var is_last_item = (i === items.length - 1);
            if (is_last_item || items[i].genus !== items[i + 1].genus) {
                break;
            }
            else {
                rows += 1;
            }
        }

        return rows;
    };

    methods.get_image = function(item, image_type) {
        /* From a species JSON record, return the first image
           encountered with the specified image type.  If no images of
           that type exist, return the first image. */

        var images = item.images;
        for (var i = 0; i < images.length; i++)
            if (images[i].type == image_type)
                return images[i];
        return images[0];
    };

    methods.display_in_list_view = function(items) {
        /* Display plant results in a list view. Use a table, with hidden
           caption and header row for accessibility. */

        $('.plant.in-results').removeClass('in-results');
        $('.plant-list table').remove();

        var html =
            '<caption class="hidden">List of matching plants</caption>' +
            '<tr class="hidden"><th>Genus</th><th>Scientific Name</th>' +
            '<th>Common Name</th><th>Details</th></tr>';
        var i;
        for (i = 0; i < items.length; i++) {
            if (i > 0) {
                html += '<tr>';
            }
            else {
                html += '<tr class="first-visible">';
            }
            var plant = items[i];
            if (i === 0 || (plant.genus !== items[i - 1].genus)) {
                var rowspan = this.get_number_of_rows_to_span(items, i);
                html += '<td class="genus" rowspan="' + String(rowspan) +
                    '">Genus: ' + plant.genus + '</td>';
            }
            html += '<td class="scientific-name">';
            var image = this.get_image(plant, 'habit');
            if (image !== undefined) {
                html += '<a href="' + image.large_thumb_url + '" ' +
                        'title="Photo">' +
                        '<img src="/static/images/icons/icon-camera.png" ' +
                        'alt=""></a>';
            }
            html += plant.scientific_name + '</td>';
            html += '<td class="common-name">' + plant.common_name +
                '</td>';
            html += '<td class="details"><a href="' +
                plant.url + '">Details</a></td>';
            html += '</tr>';
        }

        $('<table>', {'html': html}).appendTo(this.plant_list);

        /* Remove any explicit style="height: ..." that might be left
           over from image animations, since it will not apply to the
           list format. */
        $('.plant-list').removeAttr('style');

        Shadowbox.setup('.plant-list table td.scientific-name a',
                        {title: ''});
    };

    methods.create_plant_divs = function(species_list) {
        // Sort the species so the plant divs are created in the correct
        // initial order for display in the UI, where they are to appear
        // sorted alphabetically by scientific name and grouped by genus.
        var sorted_species_list = species_list.sort(function(a, b) {
            return a.scientific_name < b.scientific_name ? -1 : 1;
        });

        var WIDTH = 160 + 18;
        var HEIGHT = 210 + 4;

        for (var i = 0; i < sorted_species_list.length; i++) {
            var species = sorted_species_list[i];

            var $plant = $('<div>', {'class': 'plant'}
                          ).appendTo(this.plant_list);

            var plant_link = $('<a>', {'href': species.url}).appendTo($plant);
            $('<div>', {'class': 'frame'}).appendTo(plant_link);

            var image_container = $('<div>', {'class': 'plant-img-container'}
                                   ).appendTo(plant_link);
            var $image = $('<img>', {'alt': ''}).appendTo(image_container);
            $image.attr('x-plant-id', species.scientific_name);
            var thumb_url = this.default_image(species).thumb_url;
            if (thumb_url)  // undefined when no image available
                $image.attr('data-lazy-img-src', thumb_url);  // lazy_images

            var name_html = '<span class="latin">' +
                species.scientific_name + '</span>';
            if (species.common_name) {
                name_html += ' ' + species.common_name;
            }
            $('<p>', {'class': 'plant-name', 'html': name_html})
                .appendTo(plant_link);

            plantpreview_popup.connect(
                plant_link, species.scientific_name, this.pile_slug);

            this.plant_data.push(species);
            this.plant_divs.push($plant);
        }
        this.plant_divs_ready.resolve();
    };

    methods.display_in_grid_view = function(items) {
        /* Display plant results as a grid of photo thumbnails with
           captions. */

        $('.plant-list table').remove();

        var visible_species = {};
        for (var i = 0; i < items.length; i++)
            visible_species[items[i].id] = 1;

        var SPECIES_PER_ROW = 4;
        var WIDTH = 178;
        var HEIGHT = 232;

        var displayed_plants = [];
        var displayed_divs = [];

        var n = 0;  // count of plants actually displayed
        for (var i = 0; i < this.plant_divs.length; i++) {

            var plant = this.plant_data[i];
            var $div = this.plant_divs[i];

            if (visible_species[plant.id] === 1) {
                displayed_plants.push(plant);
                displayed_divs.push($div);

                var destx = WIDTH * (n % SPECIES_PER_ROW);
                var desty = HEIGHT * Math.floor(n / SPECIES_PER_ROW);
                n += 1;

                $div.removeClass('genus_alt');
                $div.removeClass('genus_join_left');
                $div.removeClass('genus_join_right');

                if (!$div.hasClass('in-results')) {
                    // bring new species in from the far right
                    $div.addClass('in-results');
                    $div.css({left: 2800, top: desty});
                    $div.animate({left: destx});
                } else {
                    // move the species from its current screen location
                    $div.animate({left: destx, top: desty});
                }
            } else {
                $div.removeClass('in-results');
            }
        }
        var species_section_helper = this;
        this.plant_list.animate(
            {height: desty + HEIGHT},
            function() {
                lazy_images.load();

                // Set up genus colors now that everyone has arrived!
                var last_species_in_row = SPECIES_PER_ROW - 1;
                var genus_alt = false;
                var plant = displayed_plants[0];

                for (var n = 0; n < displayed_plants.length; n++) {
                    var $div = displayed_divs[n];
                    if (genus_alt)
                        $div.addClass('genus_alt');
                    if (n < displayed_plants.length - 1) {
                        var genus = plant.genus;
                        var plant = displayed_plants[n + 1];
                        if (plant.genus === genus) {
                            if (n % SPECIES_PER_ROW != last_species_in_row) {
                                $div.addClass('genus_join_right');
                                displayed_divs[n + 1].addClass(
                                    'genus_join_left');
                            }
                        } else {
                            genus_alt = ! genus_alt;
                        }
                    }
                }
            }
        );
    };

    methods.display_results = function() {

        query_results = App3.filtered_sorted_taxadata;

        // Remove the "wait" spinner.
        this.plant_list.find('.wait').remove();

        // Display the results in the appropriate tab view.
        if (App3.show_list)
            this.display_in_list_view(query_results);
        else if (App3.show_grid) {
            this.display_in_grid_view(query_results);
            this.populate_image_types(query_results);
            lazy_images.load();
        }

        // Show the "See a list" (or "See photos") link.
        $('.list-all').removeClass('hidden');
    };

    methods.populate_image_types = function(query_results) {
        var menu_config = results_photo_menu[this.pile_slug];

        var image_list = _.flatten(_.pluck(query_results, 'images'));
        var all_image_types = _.uniq(_.pluck(image_list, 'type'));
        var image_types = _.difference(all_image_types, menu_config['omit']);

        // Add image types to the <select> and set the default value.
        image_types.sort();

        if (_.isEqual(App3.image_types.get('content'), image_types))
            // Avoid generating events when nothing has changed.
            return;

        App3.image_types.set('content', image_types);

        var old = App3.get('image_type');
        if (image_types.indexOf(old) === -1) {
            var default_type = menu_config['default'];
            if (image_types.indexOf(default_type) === -1)
                default_type = image_types[0];
            App3.set('image_type', default_type);
        }
    };

    // Return

    return SpeciesSection;
});

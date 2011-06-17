// Global declaration for JSLint (http://www.jslint.com/)
/*global window, document, clearTimeout, setTimeout, dojo, dijit, gobotany,
  global_setSidebarHeight */

dojo.provide('gobotany.sk.SpeciesSectionHelper');

dojo.require('dojo.html');
dojo.require('dijit.Dialog');
dojo.require('dijit.form.Button');
dojo.require('gobotany.sk.plant_preview');

dojo.declare('gobotany.sk.SpeciesSectionHelper', null, {

    constructor: function(results_helper) {
        "use strict";
        // summary:
        //   Manages the species section of the results page
        // results_helper:
        //   An instance of gobotany.sk.results.ResultsHelper

        this.results_helper = results_helper;
        this.scroll_event_handle = null;
    },

    setup_section: function() {
        "use strict";

        var SCROLL_WAIT_MS = 0, scroll_timer,
            RESIZE_WAIT_MS = 0, resize_timer;

        // We need to perform a fresh species query whenever a filter
        // value changes anywhere on the page.
        dojo.subscribe('/sk/filter/change', this, 'perform_query');

        // Call the lazy image loader when the page loads.
        this.lazy_load_images();

        // Assign other events that will trigger the lazy image loader,
        // with timers so as not to suffer multiple continuous event firings.

        // No delay for scrolling allows images to load during the pressing
        // and holding of a cursor key.
        dojo.connect(window, 'onscroll', this, function() {
            clearTimeout(scroll_timer);
            scroll_timer = setTimeout(this.lazy_load_images, SCROLL_WAIT_MS);
        });

        dojo.connect(window, 'onresize', this, function() {
            clearTimeout(resize_timer);
            resize_timer = setTimeout(this.lazy_load_images, RESIZE_WAIT_MS);
        });
    },

    perform_query: function() {
        "use strict";

        var plant_list = dojo.query('#main .plant-list')[0];

        // Unbind the prior scroll event handler
        if (this.scroll_event_handle) {
            dojo.disconnect(this.scroll_event_handle);
        }

        dojo.empty(plant_list);

        this.results_helper.filter_manager.perform_query({
            on_complete: dojo.hitch(this, 'on_complete_perform_query')
        });

        this.results_helper.save_filter_state();
    },

    on_complete_perform_query: function(data) {
        "use strict";

        var plant_list, see_list;
            
        plant_list = dojo.query('#main .plant-list')[0];

        // Update the species count everywhere it appears on the screen.
        dojo.query('.species-count').html(String(data.items.length));

        // Show the "Show" drop-down menu.
        show_menu = dojo.query('.show')[0];
        dojo.removeClass(show_menu, 'hidden');

        this.display_results(data.items, plant_list);

        // Show the "See a list" link.
        see_list = dojo.query('.list-all')[0];
        dojo.removeClass(see_list, 'hidden');

        global_setSidebarHeight();

        // Signal the "Show:" button to scrape our data to discover what
        // kinds of thumbnail images are available.
        dojo.publish('results_loaded',
                     [{filter_manager: this.results_helper.filter_manager,
                       data: data}]);

        this.results_helper.species_section.lazy_load_images();
    },

    organize_by_genera: function(items) {
        "use strict";

        var genera = [], genus = '', species = [], i, genus_with_species;

        // Build a data structure convenient for iterating over genera with
        // species for each.
        for (i = 0; i < items.length; i += 1) {
            if ((i > 0) && (items[i].genus !== genus)) {
                // There's a new genus, so add the prior genus and species to
                // to the genera list.
                genus_with_species = {
                    'genus': genus,
                    'species': species
                };
                genera.push(genus_with_species);
                // Clear the species list for the new genus.
                species = [];
            }
            genus = items[i].genus;
            species.push(items[i]);
        }
        // Add the last genus with its species.
        genera.push({'genus': genus, 'species': species});

        return genera;
    },

    default_image: function(species) {
        "use strict";

        var i, image;

        for (i = 0; i < species.images.length; i += 1) {
            image = species.images[i];
            if (image.rank === 1 && image.type === 'habit') {
                return image;
            }
        }
        return {};
    },

    connect_plant_preview_popup: function(plant_link, species, pile_slug) {
        "use strict";

        dojo.connect(plant_link, 'onclick', species, function(event) {
            event.preventDefault();
            var plant = this;
            dijit.byId('plant-preview').show();
            gobotany.sk.plant_preview.show(
                plant,
                {'pile_slug': pile_slug});
        });
    },

    display_results: function(items, plants_container) {
        "use strict";

        var SPECIES_PER_ROW = 4, NUM_GENUS_COLORS = 5, genus_color = 1,
            num_rows = Math.ceil(items.length / SPECIES_PER_ROW), r,
            class_value, row, s, species, plant_class_value, plant, path, url,
            plant_link, image_container, image, thumb_url, name_html,
            pile_slug;

        for (r = 0; r < num_rows; r += 1) {
            class_value = 'row';
            if (r === num_rows - 1) {
                class_value += ' last';
            }
            row = dojo.create('div', {'class': class_value});

            // Add the species for this row.
            for (s = r * SPECIES_PER_ROW;
                 s < (r * SPECIES_PER_ROW) + SPECIES_PER_ROW; s += 1) {

                if (items[s] !== undefined) {
                    species = items[s];
                    plant_class_value = 'plant';
                    if (s === (r * SPECIES_PER_ROW)) {
                        plant_class_value += ' first';
                    }
                    else if ((s === (r * SPECIES_PER_ROW) +
                                     SPECIES_PER_ROW - 1) ||
                            (items[s + 1] === undefined)) {
                        plant_class_value += ' last';
                    }

                    // Set a background color, changing color if a new genus.
                    if (s > 0) {
                        if (items[s].genus !== items[s - 1].genus) {
                            genus_color += 1;
                            if (genus_color > NUM_GENUS_COLORS) {
                                genus_color = 1;
                            }
                        }
                    }
                    plant_class_value += ' genus' + String(genus_color);

                    plant = dojo.create('div',
                        {'class': plant_class_value});
                    path = window.location.pathname.split('#')[0];
                    url = (path + species.scientific_name.toLowerCase()
                           .replace(' ', '/') + '/');
                    plant_link = dojo.create('a', {'href': url});
                    dojo.create('div', {'class': 'frame'}, plant_link);

                    image_container = dojo.create('div',
                        {'class': 'img-container'});
                    image = dojo.create('img', {'alt': ''});
                    dojo.attr(image, 'x-plant-id',
                              species.scientific_name);
                    thumb_url = this.default_image(species).thumb_url;
                    if (thumb_url) { // undefined when no image available
                        // Set the image URL in a dummy attribute, so we
                        // can lazy load images, switching to the proper
                        // attribute when the image comes into view.
                        dojo.attr(image, 'x-tmp-src', thumb_url);
                    }
                    dojo.place(image, image_container);
                    dojo.place(image_container, plant_link);

                    name_html = '<span class="latin">' +
                        species.scientific_name + '</span>';
                    if (species.common_name) {
                        name_html += ' ' + species.common_name;
                    }
                    dojo.create('p', {'class': 'plant-name',
                        'innerHTML': name_html}, plant_link);

                    // Connect a "plant preview" popup. Pass species as
                    // context in the connect function, which becomes
                    // 'this' to pass along as the variable plant.
                    pile_slug = this.results_helper.pile_slug;
                    this.connect_plant_preview_popup(plant_link, species,
                        pile_slug);

                    dojo.place(plant_link, plant);
                    dojo.place(plant, row);

                    if (plant_class_value.indexOf('last') > -1) {
                        dojo.create('div', {'class': 'clearit'}, row);
                    }
                }
            }
            dojo.place(row, plants_container);
        }
    },

    lazy_load_images: function() {
        "use strict";
        
        var viewport, viewport_height, scroll_top, scroll_left,
            image_elements, i, element, total_offset_left, total_offset_top,
            current_element, is_element_visible, image_url;

        viewport = dijit.getViewport();
        viewport_height = viewport.h;
        scroll_top = 0;
        scroll_left = 0;

        if (window.pageYOffset || window.pageXOffset) {
            scroll_top = window.pageYOffset;
            scroll_left = window.pageXOffset;
        }
        else if (document.documentElement &&
                 document.documentElement.scrollTop) {
            scroll_top = document.documentElement.scrollTop;
            scroll_left = document.documentElement.scrollLeft;
        }
        else if (document.body) {
            scroll_top = document.body.scrollTop;
            scroll_left = document.body.scrollLeft;
        }

        image_elements = dojo.query('div.plant-list img');
        for (i = 0; i < image_elements.length; i += 1) {
            element = image_elements[i];
            if (element.style.visibility !== 'hidden' &&
                element.style.display !== 'none') {
                
                current_element = element;
                total_offset_left = current_element.offsetLeft;
                total_offset_top = current_element.offsetTop;

                while (current_element.offsetParent !== null) {
                    current_element = current_element.offsetParent;
                    total_offset_left += current_element.offsetLeft;
                    total_offset_top += current_element.offsetTop;
                }

                is_element_visible = false;
                // Only worry about top/bottom scroll visibility, not also
                // left/right scroll visibility.
                if (total_offset_top > (scroll_top - element.height) &&
                    total_offset_top < (viewport_height + scroll_top)) {

                    is_element_visible = true;
                }

                if (is_element_visible === true) {
                    image_url = dojo.attr(element, 'x-tmp-src');

                    // Set the attribute that will make the image load.
                    dojo.attr(element, 'src', image_url);
                }
            }
        }
    }

});

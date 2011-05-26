// Global declaration for JSLint (http://www.jslint.com/)
/*global dojo, dijit, gobotany, _global_setSidebarHeight */

dojo.provide('gobotany.sk.results.SpeciesSectionHelper');

dojo.require('dojo.html');
dojo.require('dijit.Dialog');
dojo.require('dijit.form.Button');
dojo.require('gobotany.sk.plant_preview');

dojo.declare('gobotany.sk.results.SpeciesSectionHelper', null, {
    genus_to_family: {},
    PAGE_COUNT: 12,

    constructor: function(results_helper) {
        // summary:
        //   Manages the species section of the results page
        // results_helper:
        //   An instance of gobotany.sk.results.ResultsHelper

        this.results_helper = results_helper;
        this.scroll_event_handle = null;
    },

    setup_section: function() {
        // Call the lazy image loader when the page loads.
        this.lazy_load_images();

        // Assign other events that will trigger the lazy image loader,
        // with timers so as not to suffer multiple continuous event firings.
        var scroll_timer;
        dojo.connect(window, 'onscroll', this, function() {
            clearTimeout(scroll_timer);
            scroll_timer = setTimeout(this.lazy_load_images, 500);
        });

        var resize_timer;
        dojo.connect(window, 'onresize', this, function() {
            clearTimeout(resize_timer);
            resize_timer = setTimeout(this.lazy_load_images, 500);
        });
    },

    perform_query: function() {
        // Unbind the prior scroll event handler
        if (this.scroll_event_handle) {
            dojo.disconnect(this.scroll_event_handle);
        }

        var plant_list = dojo.query('#main .plant-list')[0];
        dojo.empty(plant_list);

        // Build a list of short names for the filters visible at left (which
        // is the same as the internal collection of filters).
        var filter_short_names = [];
        var filters = this.results_helper.filter_manager.filters;
        var i;
        for (i = 0; i < filters.length; i++) {
            filter_short_names.push(filters[i].character_short_name);
        }

        // Run the query, passing a callback function to be run when finished.
        // Also pass the list of filter short names for which to get counts.
        this.results_helper.filter_manager.perform_query({
            on_complete: dojo.hitch(this, this.on_complete_perform_query),
            filter_short_names: filter_short_names
        });

        this.results_helper.save_filter_state();
    },


    rebuild_family_select: function(items) {

        // Does sort | uniq really have to be this painful in JavaScript?

        var families_seen = {};
        var family_list = [];
        var i;
        for (i = 0; i < items.length; i++) {
            var item = items[i];
            if (! families_seen[item.family]) {
                family_list.push(item.family);
                families_seen[item.family] = true;
            }
        }

        family_list.sort();

        // Update the Family data store.

        var family_select = dijit.byId('family_select');
        var family_store = family_select.store;

        family_store.fetch({onComplete: dojo.hitch(this, function(items) {
            var i;
            for (i = 0; i < items.length; i++) {
                family_store.deleteItem(items[i]);
            }
            family_store.save();
            for (i = 0; i < family_list.length; i++) {
                var f = family_list[i];
                family_store.newItem({ name: f, family: f });
            }
            family_store.save();

            var fm = this.results_helper.filter_manager;
            var v = fm.get_selected_value('family');
            if (v) {
                family_select.set('value', v);
            }
        })});
    },

    rebuild_genus_select: function(items) {
        // Does sort | uniq really have to be this painful in JavaScript?

        var genera_seen = {};
        var genus_list = [];
        var i;
        for (i = 0; i < items.length; i++) {
            var item = items[i];
            if (! genera_seen[item.genus]) {
                genus_list.push(item.genus);
                genera_seen[item.genus] = true;
                this.genus_to_family[item.genus] = item.family;
            }
        }

        genus_list.sort();

        // Update the Genus data store.

        var genus_select = dijit.byId('genus_select');
        var genus_store = genus_select.store;

        genus_store.fetch({onComplete: dojo.hitch(this, function(items) {
            var i;
            for (i = 0; i < items.length; i++) {
                genus_store.deleteItem(items[i]);
            }
            genus_store.save();
            for (i = 0; i < genus_list.length; i++) {
                var g = genus_list[i];
                genus_store.newItem({ name: g, genus: g });
            }
            genus_store.save();

            var fm = this.results_helper.filter_manager;
            var v = fm.get_selected_value('genus');
            if (v) {
                genus_select.set('value', v);
            }
        })});
    },

    on_complete_perform_query: function(data) {
        this.rebuild_family_select(data.items);
        this.rebuild_genus_select(data.items);

        // Update the species count on the screen.
        var count_elements = dojo.query('.species-count');
        var i;
        for (i = 0; i < count_elements.length; i++) {
            count_elements[i].innerHTML = data.items.length;
        }

        // If the filter working area is showing, refresh its display in order
        // to update any value counts.
        var working_area = dojo.query('div.working-area')[0];
        if (dojo.style(working_area, 'display') === 'block') {
            var short_name = this.results_helper.filter_section
                .visible_filter_short_name;
            var filter = this.results_helper.filter_manager.get_filter(
                short_name);
            if (filter !== null) {
                this.results_helper.filter_section.show_filter_working(
                    filter);
            }
        }

        var plant_list = dojo.query('#main .plant-list')[0];
        this.display_results(data.items, plant_list);

        _global_setSidebarHeight();

        // Signal the "Show:" button to scrape our data to discover what
        // kinds of thumbnail images are available.
        dojo.publish('results_loaded',
                     [{filter_manager: this.results_helper.filter_manager,
                       data: data}]);

        this.results_helper.species_section.lazy_load_images();
    },

    organize_by_genera: function(items) {
        // Build a data structure convenient for iterating over genera with
        // species for each.
        var genera = [];
        var genus = '';
        var species = [];
        var i;
        for (i = 0; i < items.length; i++) {
            if ((i > 0) && (items[i].genus !== genus)) {
                // There's a new genus, so add the prior genus and species to
                // to the genera list.
                var genus_with_species = {
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
        var i;
        for (i = 0; i < species.images.length; i++) {
            var image = species.images[i];
            if (image.rank === 1 && image.type === 'habit') {
                return image;
            }
        }
        return {};
    },

    connect_plant_preview_popup: function(plant_link, species, pile_slug) {
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
        var SPECIES_PER_ROW = 4;
        var num_rows = Math.ceil(items.length / SPECIES_PER_ROW);
        var r;
        for (r = 0; r < num_rows; r++) {
            // Temporarily continue using the 'genus' container, until some
            // refactoring can be done. Use one per row.
            var class_value = 'genus';
            if (r === num_rows - 1) {
                class_value += ' last';
            }
            var genus_container = dojo.create('div', {
                'class': class_value
            });

            var row_class_value = 'row';
            if (r === num_rows - 1) {
                row_class_value += ' last';
            }
            var row = dojo.create('div', {'class': row_class_value});

            // Add the species for this row.
            var s;
            for (s = r * SPECIES_PER_ROW;
                 s < (r * SPECIES_PER_ROW) + SPECIES_PER_ROW; s++) {
                
                if (items[s] !== undefined) {
                    var species = items[s];
                    var plant_class_value = 'plant';
                    if ((s === (r * SPECIES_PER_ROW) + SPECIES_PER_ROW - 1) ||
                            (items[s + 1] === undefined)) {                
                        plant_class_value += ' last';
                    }
                    var plant = dojo.create('div',
                        {'class': plant_class_value});
                    var path = window.location.pathname.split('#')[0];
                    var url = (path + species.scientific_name.toLowerCase()
                               .replace(' ', '/') + '/');
                    var plant_link = dojo.create('a', {'href': url});
                    dojo.create('div', {'class': 'frame'}, plant_link);

                    var image_container = dojo.create('div',
                        {'class': 'img-container'});
                    var image = dojo.create('img', {'alt': ''});
                    dojo.attr(image, 'x-plant-id',
                              species.scientific_name);
                    var thumb_url = this.default_image(species).thumb_url;
                    if (thumb_url) { // undefined when no image available
                        // Set the image URL in a dummy attribute, so we
                        // can lazy load images, switching to the proper
                        // attribute when the image comes into view.
                        dojo.attr(image, 'x-tmp-src', thumb_url);
                    }
                    dojo.place(image, image_container);
                    dojo.place(image_container, plant_link);

                    var name_html = '<span class="latin">' +
                        species.scientific_name + '</span>';
                    if (species.common_name) {
                        name_html += ' ' + species.common_name;
                    }
                    dojo.create('p', {'class': 'plant-name',
                        'innerHTML': name_html}, plant_link);

                    // Connect a "plant preview" popup. Pass species as
                    // context in the connect function, which becomes
                    // 'this' to pass along as the variable plant.
                    var pile_slug = this.results_helper.pile_slug;
                    this.connect_plant_preview_popup(plant_link, species,
                        pile_slug);

                    dojo.place(plant_link, plant);
                    dojo.place(plant, row);

                    if (plant_class_value.indexOf('last') > -1) {
                        dojo.create('div', {'class': 'clearit'}, row);
                    }
                }
            }
            dojo.place(row, genus_container);
            dojo.place(genus_container, plants_container);
        }    
    },

    lazy_load_images: function() {
        var viewport = dijit.getViewport();
        var viewport_height = viewport.h;
        var viewport_width = viewport.w;
        //console.log('viewport_height: ' + viewport_height +
        //            ' viewport_width: ' + viewport_width);

        var scroll_top = 0;
        var scroll_left = 0;
        if (window.pageYOffset || window.pageXOffset) {
            scroll_top = window.pageYOffset;
            scroll_left = window.pageXOffset;
	    }
        /*else if (dojo.exists(document, 'documentElement.scrollTop')) {
            scroll_top = document.documentElement.scrollTop;
            scroll_left = document.documentElement.scrollLeft;
	    } <-- FIXME: fires an error on loading sometimes; doc not ready yet? */ 
        else if (document.body) {
		    scroll_top = document.body.scrollTop;
            scroll_left = document.body.scrollLeft;
	    }
        //console.log('scroll_top: ' + scroll_top +
        //            ' scroll_left: ' + scroll_left);

        var image_elements = dojo.query('div.plant-list img');
        var i;
        for (i = 0; i < image_elements.length; i++) {
            var element = image_elements[i];
            if (element.style.visibility !== 'hidden' && 
                element.style.display !== 'none') {

                var total_offset_left = 0;
                var total_offset_top = 0;
                var current_element = element;
                do {
                    total_offset_left += current_element.offsetLeft;
                    total_offset_top += current_element.offsetTop;
                }
                while (current_element = current_element.offsetParent)

                var is_element_visible = false;
                // Only worry about top/bottom scroll visibility, not
                // left/right scroll visibility.
                if (total_offset_top > (scroll_top - element.height) &&
                    total_offset_top < viewport_height + scroll_top) {

                    is_element_visible = true;
                }

                if (is_element_visible === true) {
                    var image_url = dojo.attr(element, 'x-tmp-src');

                    /*
                    // Write a console message
                    var message = image_url + ':';
                    message += ' total_offset_top: ' + total_offset_top;
                    message += ' total_offset_left: ' + total_offset_left;
                    message += ' is_element_visible: ' + is_element_visible;
                    console.log(message);
                    */

                    // Set the src attribute so the image will load.
                    dojo.attr(element, 'src', image_url);
                }
            }
        }
    }

});

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
        var genera = this.organize_by_genera(items);

        var SPECIES_PER_ROW = 4;
        var i;
        for (i = 0; i < genera.length; i++) {
            var class_value = 'genus';
            if ((i + 1) % 2) {
                class_value += ' odd';
            }
            else {
                class_value += ' even';
            }
            if (i === genera.length - 1) {
                class_value += ' last';
            }
            var genus_container = dojo.create('div', {
                'class': class_value
            });

            // Add the species for this genus.
            var genus = genera[i];
            var j;
            for (j = 0; j < genus.species.length; j += SPECIES_PER_ROW) {
                var row_class_value = 'row';
                if (j + SPECIES_PER_ROW >= genus.species.length) {
                    row_class_value = 'row last';
                }
                var row = dojo.create('div', {'class': row_class_value});

                var plant_index_in_row = 0;
                var k;
                for (k = j; k < j + SPECIES_PER_ROW; k++) {
                    if (genus.species[k] !== undefined) {
                        var species = genus.species[k];
                        var plant_class_value = 'plant';
                        if ((plant_index_in_row === SPECIES_PER_ROW - 1) ||
                            (genus.species[k + 1] === undefined)) {
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
                        if (thumb_url)  // undefined when no image available
                            dojo.attr(image, 'src', thumb_url);
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

                        plant_index_in_row++;
                    }
                }

                dojo.place(row, genus_container);
            }

            dojo.place(genus_container, plants_container);
        }
    }
});

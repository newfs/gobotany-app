// Global declaration for JSLint (http://www.jslint.com/)
/*global dojo, dijit, gobotany */

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
        dojo.empty('plant-listing');
        dojo.query('#plants .species_count .loading').removeClass('hidden');
        dojo.query('#plants .species_count .count').addClass('hidden');

        // Build a list of short names for the filters visible at left (which
        // is the same as the internal collection of filters).
        var filter_short_names = [];
        var filters = this.results_helper.filter_manager.filters;
        for (var i = 0; i < filters.length; i++) {
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

        for (var i = 0; i < items.length; i++) {
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
            for (var i = 0; i < items.length; i++) {
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

        for (var i = 0; i < items.length; i++) {
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
            for (var i = 0; i < items.length; i++) {
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
        dojo.query('#plants .species_count .count .number')[0].innerHTML =
            data.items.length;
        dojo.query('#plants .species_count .loading').addClass('hidden');
        dojo.query('#plants .species_count .count').removeClass('hidden');

        // If the filter working area is showing, refresh its display in order
        // to update any value counts.
        if (dojo.style('filter-working', 'display') === 'block') {
            var short_name = this.results_helper.filter_section
                .visible_filter_short_name;
            var filter = this.results_helper.filter_manager.get_filter(
                short_name);
            if (filter !== null) {
                this.results_helper.filter_section.show_filter_working(
                    filter);
            }
        }

        // Clear display
        var plant_listing = dojo.byId('plant-listing');
        this.paginate_results(data.items, plant_listing);

        // Define the pages here to make the event handler a bit more efficient
        // Bind a handler to load images on scroll
        var plant_scrollable = dojo.byId('plants');
        var plant_pages = dojo.query('li.PlantScrollPage[x-loaded=false]',
                                     plant_listing);
        this.scroll_event_handle = dojo.connect(plant_scrollable, 'onscroll',
            dojo.hitch(this, function() {
                plant_pages.forEach(dojo.hitch(
                    this, this.load_page_if_visible));
            }));
        dojo.publish('results_loaded',
                     [{filter_manager: this.results_helper.filter_manager,
                       data: data}]);
    },

    paginate_results: function(items, start) {
        var page;
        var page_num;
        var list;
        var previous_genus = 'this string matches no actual genus';
        var genus_number = -1;  // incremented each time we reach a new genus
        for (var i = 0; i < items.length; i++) {
            var item = items[i];
            if (item.genus != previous_genus) {
                genus_number++;
                previous_genus = item.genus;
            }
            var remainder = i % this.PAGE_COUNT;
            if (remainder === 0) {
                page_num = ((i - remainder) / this.PAGE_COUNT) + 1;
                page = dojo.create('li', {
                    'class': 'PlantScrollPage',
                    id: 'plant-page-' + page_num.toString()
                }, start);
                dojo.html.set(page, 'Page ' + page_num.toString());
                list = dojo.create('ul', {}, page);
                // All items on the first page have been loaded
                dojo.attr(page, 'x-loaded', page_num == 1 ? 'true' : 'false');
            }
            var partial = (page_num !== 1);
            this.render_item(item, list, genus_number, partial, this);
        }
        return start;
    },

    render_item: function(item, start_node, genus_number, partial,
                          species_section) {
        // Fill in the search list with anchors, images and titles
        var genus_colors = 4;  // alternate between two colors for genera
        var li_node = dojo.create('li', {
            'id': 'plant-' + item.scientific_name.toLowerCase()
                .replace(/\W/, '-'),
            'class': 'genus' + (genus_number % genus_colors).toString()
        }, start_node);
        var anchor = dojo.create('a', {href: '#'}, li_node);
        var image = item.default_image;
        var img;
        if (image) {
            img = dojo.create('img', {height: image.thumb_height,
                                      width: image.thumb_width,
                                      alt: image.title,
                                      'x-plant-id': item.scientific_name},
                              anchor);
            // If a partial rendering was requested,
            // set a secret attribute instead of src
            // We can use that to fill src when scrolling
            var img_attr = partial ? 'x-tmp-src' : 'src';
            dojo.attr(img, img_attr, image.thumb_url);
            dojo.style(img, 'height', image.thumb_height);
        } else {
            dojo.create('span', {'class': 'MissingImage'},anchor);
        }
        var title = dojo.create('span', {'class': 'PlantTitle'}, anchor);
        dojo.html.set(title, item.scientific_name);

        var pile_slug = this.results_helper.pile_slug;

        // Connect the click event last so it's possible to pass the image node.
        dojo.connect(li_node, 'onclick', item, function(event) {
            event.preventDefault();
            dijit.byId('plant-preview').show();
            var plant = this;
            gobotany.sk.plant_preview.show(plant,
                {'pile_slug': pile_slug,
                 'clicked_image_alt_text': dojo.attr(img, 'alt')});
        });
    },

    load_page: function(page) {
        var images = dojo.query('img[src=]', page);
        images.forEach(function(image, i) {
            dojo.attr(image, 'src', dojo.attr(image, 'x-tmp-src'));
        });
        dojo.attr(page, 'x-loaded', 'true');
    },

    load_page_if_visible: function(page) {
        // Don't load a page if it's already loaded
        if (dojo.attr(page, 'x-loaded') == 'true') { return; }
        // Check to see if the page is inside the parent viewport
        var container_pos = dojo.position(dojo.byId('plants'), false);
        var page_pos = dojo.position(page, false).y;
        if (container_pos.h >= (page_pos - container_pos.y)) {
            this.load_page(page);
        }
    }
});

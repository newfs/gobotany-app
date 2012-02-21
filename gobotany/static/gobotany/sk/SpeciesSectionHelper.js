dojo.provide('gobotany.sk.SpeciesSectionHelper');

dojo.require('dojo.hash');
dojo.require('dojo.html');
dojo.require('dojo.NodeList-fx');
dojo.require('dojox.data.JsonRestStore');
dojo.require('dijit.Dialog');
dojo.require('dijit.form.Button');
dojo.require('gobotany.utils');

dojo.declare('gobotany.sk.SpeciesSectionHelper', null, {

    plant_preview_characters: null,  // set by results.js during page load
    default_filters: null,           // set by results.js during page load

    constructor: function(results_helper) {
        'use strict';
        // summary:
        //   Manages the species section of the results page
        // results_helper:
        //   An instance of gobotany.sk.results.ResultsHelper

        this.PHOTOS_VIEW = 'photos';
        this.LIST_VIEW = 'list';
        this.animation = null;
        this.plant_list = dojo.query('#main .plant-list')[0];
        this.plant_data = [];
        this.plant_divs = [];
        this.plant_divs_displayed_yet = false;
        this.query_results = [];  // list of speciecs info objects
        this.results_helper = results_helper;
        this.scroll_event_handle = null;
        this.current_view = this.PHOTOS_VIEW;
        this.show_photos_type = null;

        simplekey_resources.pile_species(this.results_helper.pile_slug).done(
            dojo.hitch(this, 'create_plant_divs')
        );
        dojo.subscribe('/filters/query-result', this, 'on_query_result');
    },

    setup_section: function() {
        'use strict';

        // Call the lazy image loader when the page loads.
        this.lazy_load_images();

        // Assign other events that will trigger the lazy image loader,
        // with timers so as not to suffer a quick succession of multiple
        // event firings.

        // No delay for scrolling allows images to load during the pressing
        // and holding of a cursor key.
        var SCROLL_WAIT_MS = 0;
        var scroll_timer;
        dojo.connect(window, 'onscroll', this, function() {
            clearTimeout(scroll_timer);
            scroll_timer = setTimeout(this.lazy_load_images, SCROLL_WAIT_MS);
        });

        var RESIZE_WAIT_MS = 500;
        var resize_timer;
        dojo.connect(window, 'onresize', this, function() {
            clearTimeout(resize_timer);
            resize_timer = setTimeout(this.lazy_load_images, RESIZE_WAIT_MS);
        });

        // Wire up tabs and a link for toggling between photo and list views.
        dojo.query('#results-tabs a').onclick(this, this.toggle_view);

        var view_toggle_link = dojo.query('.list-all a')[0];
        dojo.connect(view_toggle_link, 'onclick', this, this.toggle_view);

        // Set the initial view for showing the results.
        var hash_object = dojo.queryToObject(dojo.hash());
        if (hash_object._view !== undefined) {
            this.current_view = hash_object._view;
            this.set_navigation_to_view(this.current_view);
        }
    },

    on_query_result: function(message) {
        'use strict';

        // Unbind the prior scroll event handler
        if (this.scroll_event_handle)
            dojo.disconnect(this.scroll_event_handle);

        // Save the results.
        this.query_results = message.species_list;

        // Display the results.
        this.display_results();

        // Save the current state of our filters.
        this.results_helper.save_filter_state();
    },

    default_image: function(species) {
        'use strict';

        var i;
        for (i = 0; i < species.images.length; i += 1) {
            var image = species.images[i];
            if (image.rank === 1 && image.type === 'habit') {
                return image;
            }
        }
        return {};
    },

    sort_character_list: function(a, b) {
        var FRIENDLY_NAME_KEY = 'friendly_name';
        // Custom sort function for sorting the combined character list.
        if (a[FRIENDLY_NAME_KEY] > b[FRIENDLY_NAME_KEY]) {
            return 1;
        }
        if (a[FRIENDLY_NAME_KEY] < b[FRIENDLY_NAME_KEY]) {
            return -1;
        }
        return 0;
    },

    get_character_list: function(plant_preview_characters) {
        var characters = [];
        characters = characters.concat(plant_preview_characters);
        return characters.sort(this.sort_character_list);
    },

    get_multivalue_list: function(display_value, is_compact) {
        // Return a HTML list for presenting multiple character values.
        var list, i;
        
        if (typeof(display_value) !== 'string') {
            list = '<ul';
            if (is_compact) {
                list += ' class="compact"';
            }                
            list +='>';
            for (i = 0; i < display_value.length; i++) {
                list += '<li';
                if (i === display_value.length - 1) {
                    list += ' class="last"';
                }
                list +='>' + display_value[i] + '</li>';
            }
            list += '</ul>';
        }
        else {
            list = display_value;
        }
        
        return list;
    },

    connect_plant_preview_popup: function(plant_link, plant, pile_slug) {
        'use strict';

        dojo.connect(plant_link, 'onclick', this, function(event) {
            event.preventDefault();

            // A few characters get a "compact" list for multiple values.
            var COMPACT_EX = /^habitat|habitat_general|state_distribution$/;

            // Populate the hidden content area with information about
            // this plant.
            var name = plant.scientific_name + ' <span>' +
                plant.common_name + '</span>';
            dojo.html.set(dojo.query('#plant-detail-modal h3')[0], name);

            // Call the API to get more information.
            var taxon_url = API_URL + 'taxon/' + plant.scientific_name + '/';
            var taxon_store = new dojox.data.JsonRestStore({
                target: taxon_url});
            taxon_store.fetch({
                onComplete: dojo.hitch(this, function(taxon) {
                    // Fill in Facts About.
                    dojo.html.set(dojo.query(
                        '#plant-detail-modal div.details p.facts')[0],
                        taxon.factoid);

                    // Fill in Habitat.
                    if (taxon.habitat !== undefined) {
                        var habitat_list = taxon.habitat.sort().join(', ');
                        habitat_list = habitat_list[0].toUpperCase() +
                            habitat_list.slice(1);
                        dojo.html.set(dojo.query(
                            '#plant-detail-modal div.details p.habitat')[0],
                            habitat_list);
                    }

                    // Fill in Characteristics.
                    var characters = this.get_character_list(
                        this.plant_preview_characters);
                    var characters_html = '';
                    for (var i = 0; i < characters.length; i++) {
                        var ppc = characters[i];

                        if (ppc.partner_site === gobotany_sk_partner_site) {

                            var display_value = '';
                            var character_value =
                                taxon[ppc.character_short_name];
                            if (character_value !== undefined &&
                                character_value !== null) {

                                display_value = character_value;
                                if (ppc.value_type === 'LENGTH') {
                                    var min = character_value[0];
                                    var max = character_value[1];
                                    var min_mm = gobotany.utils.convert(
                                        min, ppc.unit, 'mm');
                                    var max_mm = gobotany.utils.convert(
                                        max, ppc.unit, 'mm');
                                    display_value =
                                        gobotany.utils.pretty_length(
                                        ppc.unit, min_mm, false) + '&#8211;' +
                                        gobotany.utils.pretty_length(
                                        ppc.unit, max_mm);
                                }
                                else {
                                    // For multiple-value characters,
                                    // make a list.
                                    if (typeof(display_value) !== 'string') {
                                       var is_compact = (COMPACT_EX.test(
                                            ppc.character_short_name));
                                        display_value =
                                            this.get_multivalue_list(
                                                display_value, is_compact);
                                    }
                                }
                            }

                            // Only display this character if it has a value.
                            if (display_value !== undefined &&
                                display_value !== '') {
                                characters_html += '<dl><dt>' +
                                    ppc.friendly_name + '</dt><dd>' +
                                    display_value + '</dd></dl>';
                            }
                        }
                    }
                    var characters_list = dojo.query(
                        '#plant-detail-modal .details .characteristics')[0];
                    dojo.html.set(characters_list, characters_html);

                    // Wire up the Get More Info button.
                    var path = window.location.pathname.split('#')[0];
                    var url = path +
                        plant.scientific_name.toLowerCase().replace(' ',
                        '/') + '/';
                    var button =
                        dojo.query('#plant-detail-modal a.get-more-info')[0];
                    dojo.attr(button, 'href', url);

                    // Add images.
                    var images_html = '';
                    var clicked_image_path = $('img', plant_link).attr('src');
                    if (clicked_image_path !== undefined) {
                        clicked_image_path = clicked_image_path.substr(
                            0, clicked_image_path.indexOf('_jpg_'));
                        var is_missing_image = $('div.missing-image',
                            plant_link).length ? true : false;
                        for (i = 0; i < taxon.images.length; i++) {
                            var taxon_image = taxon.images[i];
                            var new_image = '<img src="' +
                                taxon_image.large_thumb_url + '" alt="' +
                                taxon_image.title + '">';
                            var taxon_image_path = 
                                taxon_image.large_thumb_url;
                            taxon_image_path = taxon_image_path.substr(
                                0, taxon_image_path.indexOf('_jpg_'));
                            if (clicked_image_path === taxon_image_path &&
                                !is_missing_image) {

                                // Since this is the same image as was
                                // clicked, show it first.
                                images_html = new_image + images_html;
                            }
                            else {
                                images_html += new_image;
                            }
                        }
                    }
                    dojo.html.set(
                        dojo.query('#plant-detail-modal div.images')[0],
                        images_html);

                    // Open the Shadowbox modal dialog with a copy of the
                    // HTML in the hidden content area.
                    var content_element =
                        dojo.query('#plant-detail-modal')[0];
                    Shadowbox.open({
                        content: content_element.innerHTML,
                        player: 'html',
                        height: 650,
                        width: 880,
                        options: {onFinish: dojo.hitch(this, function() {
                            var $sb = $('#sb-container');
                            var $children = $sb.find('p, li');
                            var markup = dojo.hitch(
                                this.results_helper.filter_section
                                    .glossarizer, 'markup');

                            $sb.find('.img-container').scrollable();
                            for (var i = 0; i < $children.length; i++) {
                                markup($children[i]);
                            }
                        })}
                    });
                }
            )});
        });
    },

    set_navigation_to_view: function(view) {
        'use strict';

        var HIDDEN_CLASS = 'hidden';
        var CURRENT_TAB_CLASS = 'current';
        var photos_tab = dojo.query('#results-tabs li:first-child a')[0];
        var list_tab = dojo.query('#results-tabs li:last-child a')[0];
        var view_type = dojo.query('.list-all a span.view-type')[0];
        var photos_show_menu = dojo.query('.show')[0];       

        if (view === this.PHOTOS_VIEW) {
            dojo.removeClass(list_tab, CURRENT_TAB_CLASS);
            dojo.addClass(photos_tab, CURRENT_TAB_CLASS);
            view_type.innerHTML = 'a list of';
            dojo.removeClass(photos_show_menu, HIDDEN_CLASS);
        } else if (view === this.LIST_VIEW) {
            dojo.removeClass(photos_tab, CURRENT_TAB_CLASS);
            dojo.addClass(list_tab, CURRENT_TAB_CLASS);
            view_type.innerHTML = 'photos for';
            dojo.addClass(photos_show_menu, HIDDEN_CLASS);
        } else {
           console.log('Unknown view name: ' + view);
        }
    },

    toggle_view: function(event) {
        'use strict';
    
        if (event.target.innerHTML.toLowerCase() === this.current_view) {
            // If the same tab as the current view was clicked, do nothing.
            return;
        }

        var HIDDEN_CLASS = 'hidden';
        var CURRENT_TAB_CLASS = 'current';
        var photos_tab = dojo.query('#results-tabs li:first-child a')[0];
        var list_tab = dojo.query('#results-tabs li:last-child a')[0];
        var view_type = dojo.query('.list-all a span.view-type')[0];
        var photos_show_menu = dojo.query('.show')[0];

        if (this.current_view === this.PHOTOS_VIEW) {
            this.current_view = this.LIST_VIEW;
        } else {
            this.current_view = this.PHOTOS_VIEW;
        }

        this.set_navigation_to_view(this.current_view);
        this.display_results();
    },

    get_number_of_rows_to_span: function(items, start) {
        /* From a starting point in a list of plant items, return the number
           of rows it takes to get to the next genus (or the end of the
           list). */
        'use strict';

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
    },

    get_image: function(item, image_type) {
        /* From a species JSON record, return the first image encountered
         * with the specified image type. If no images of that type exist,
         * return the first image. */
        'use strict';
        
        var i, image_index;

        image_index = 0;   // Fallback: first image
        for (i = 0; i < item.images.length; i++) {
            if (item.images[i].type === image_type) {
                image_index = i;
                break;
            }
        }

        return item.images[image_index];
    },

    display_in_list_view: function(items) {
        /* Display plant results in a list view. Use a table, with hidden
           caption and header row for accessibility. */
        'use strict';

        dojo.query('.plant.in-results').removeClass('in-results');
        dojo.query('.plant-list table').orphan();

        var html =
            '<caption class="hidden">List of matching plants</caption>' +
            '<tr class="hidden"><th>Genus</th><th>Scientific Name</th>' +
            '<th>Common Name</th><th>Details</th></tr>';
        var i;
        for (i = 0; i < items.length; i += 1) {
            if (i > 0) {
                html += '<tr>';
            }
            else {
                html += '<tr class="first-visible">';
            }
            if (i === 0 || (items[i].genus !== items[i - 1].genus)) {
                var rowspan = this.get_number_of_rows_to_span(items, i);
                html += '<td class="genus" rowspan="' + String(rowspan) +
                    '">Genus: ' + items[i].genus + '</td>';
            }
            html += '<td class="scientific-name">';
            var image = this.get_image(items[i], 'habit');
            if (image !== undefined) {
                html += '<a href="' + image.large_thumb_url + '" ' +
                        'title="Photo">' +
                        '<img src="/static/images/icons/icon-camera.png" ' +
                        'alt=""></a>';
            }
            html += items[i].scientific_name + '</td>';
            html += '<td class="common-name">' + items[i].common_name +
                '</td>';
            html += '<td class="details"><a href="' +
                items[i].scientific_name.toLowerCase().replace(' ', '/') +
                '/">Details</a></td>';
            html += '</tr>';
        }
        
        var table = dojo.create('table', {'innerHTML': html},
                                this.plant_list);
        var table_height = table.clientHeight;
        $('.plant-list').height(table_height);

        sidebar_set_height();

        Shadowbox.setup('.plant-list table td.scientific-name a', 
                        {title: ''});
    },

    create_plant_divs: function(species_list) {
        var WIDTH = 160 + 18;
        var HEIGHT = 210 + 4;

        for (var i = 0; i < species_list.length; i++) {
            var species = species_list[i];

            var plant = dojo.create('div', {'class': 'plant'},
                                    this.plant_list);

            var path = window.location.pathname.split('#')[0];
            var url = (path + species.scientific_name.toLowerCase()
                       .replace(' ', '/') + '/');
            var plant_link = dojo.create('a', {'href': url}, plant);
            dojo.create('div', {'class': 'frame'}, plant_link);

            var image_container = dojo.create('div', {
                'class': 'img-container'
            }, plant_link);
            var image = dojo.create('img', {'alt': ''}, image_container);
            dojo.attr(image, 'x-plant-id', species.scientific_name);
            var thumb_url = this.default_image(species).thumb_url;
            if (thumb_url) { // undefined when no image available
                // Set the image URL in a dummy attribute, so we can
                // lazy-load images, switching to the proper
                // attribute when the image comes into view.
                dojo.attr(image, 'x-tmp-src', thumb_url);
            }

            var name_html = '<span class="latin">' +
                species.scientific_name + '</span>';
            if (species.common_name) {
                name_html += ' ' + species.common_name;
            }
            dojo.create('p', {'class': 'plant-name',
                              'innerHTML': name_html}, plant_link);

            // Connect a "plant preview" popup. Pass species as
            // context in the connect function, which becomes 'this'
            // to pass along as the variable plant.
            var pile_slug = this.results_helper.pile_slug;
            this.connect_plant_preview_popup(plant_link, species, pile_slug);

            this.plant_data.push(species);
            this.plant_divs.push(plant);
        }
    },

    display_in_photos_view: function(items) {
        /* Display plant results as a grid of photo thumbnails with
           captions.
           */
        'use strict';

        dojo.query('.plant-list table').orphan();

        var visible_species = {};
        for (var i = 0; i < items.length; i++)
            visible_species[items[i].id] = 1;

        var SPECIES_PER_ROW = 4;
        var WIDTH = 178;
        var HEIGHT = 232;

        var anim_list = [];
        var displayed_plants = [];
        var displayed_divs = [];

        var n = 0;  // count of plants actually displayed
        for (var i = 0; i < this.plant_divs.length; i++) {

            var plant = this.plant_data[i];
            var div = this.plant_divs[i];

            if (visible_species[plant.id] === 1) {
                displayed_plants.push(plant);
                displayed_divs.push(div);

                var destx = WIDTH * (n % SPECIES_PER_ROW);
                var desty = HEIGHT * Math.floor(n / SPECIES_PER_ROW);
                n += 1;

                dojo.removeClass(div, 'genus_alt');
                dojo.removeClass(div, 'genus_join_left');
                dojo.removeClass(div, 'genus_join_right');

                if (!dojo.hasClass(div, 'in-results')) {
                    // bring new species in from the far right
                    dojo.addClass(div, 'in-results');
                    div.style.top = desty + 'px';
                    anim_list.push(dojo.animateProperty({
                        node: div,
                        properties: {left: {
                            start: 2800,
                            end: destx
                        }}
                    }));
                } else {
                    // move the species from its current screen location
                    anim_list.push(dojo.animateProperty({
                        node: div,
                        properties: {left: {end: destx}, top: {end: desty}}
                    }));
                }
            } else {
                dojo.removeClass(div, 'in-results');
            }
        }
        anim_list.push(dojo.animateProperty({
            node: this.plant_list,
            properties: {height: {end: desty + HEIGHT}},
            onEnd: function() {
                this.animation = null;
                sidebar_set_height();

                // Set up genus colors now that everyone has arrived!
                var last_species_in_row = SPECIES_PER_ROW - 1;
                var genus_alt = false;
                var plant = displayed_plants[0];

                for (var n = 0; n < displayed_plants.length; n++) {
                    var div = displayed_divs[n];
                    if (genus_alt)
                        dojo.addClass(div, 'genus_alt');
                    if (n < displayed_plants.length - 1) {
                        var genus = plant.genus;
                        var plant = displayed_plants[n + 1];
                        if (plant.genus === genus) {
                            if (n % SPECIES_PER_ROW != last_species_in_row) {
                                dojo.addClass(div, 'genus_join_right');
                                dojo.addClass(displayed_divs[n + 1],
                                              'genus_join_left');
                            }
                        } else {
                            genus_alt = ! genus_alt;
                        }
                    }
                }
            }
        }));
        this.animation = dojo.fx.combine(anim_list);
        this.animation.play();
    },

    display_results: function() {
        'use strict';

        if (this.animation !== null) {
            this.animation.stop();
            this.animation = null;
        }

        // Show the "Show" drop-down menu for image types, if necessary.
        if (this.current_view === this.PHOTOS_VIEW) {
            var show_menu = dojo.query('.show')[0];
            dojo.removeClass(show_menu, 'hidden');
        }

        // Remove the "wait" spinner.
        dojo.query('.wait', this.plant_list).orphan();

        // Display the results in the appropriate tab view.
        if (this.current_view === this.LIST_VIEW) {
            this.display_in_list_view(this.query_results);
        }
        else {
            this.display_in_photos_view(this.query_results);
        }

        // Show the "See a list" (or "See photos") link.
        var see_link = dojo.query('.list-all')[0];
        dojo.removeClass(see_link, 'hidden');

        if (this.current_view === this.PHOTOS_VIEW) {
            // Signal the "Show:" menu to scrape our data to discover what
            // kinds of thumbnail images are available.
            dojo.publish('results_loaded',
                [{filter_manager: this.results_helper.filter_manager,
                  query_results: this.query_results}]);
            this.results_helper.species_section.lazy_load_images();
        }
    },

    lazy_load_images: function() {
        'use strict';

        // If the current view is the List view, do nothing. This allows
        // event handlers for the photos view to remain in effect without
        // awkwardly removing and adding them when the user toggles views.
        //
        // Check the DOM instead of the SpeciesSectionHelper object, because
        // when this function is called via setTimeout, the 'this' context
        // is not what we need, and passing a saved reference to 'this', as
        // recommended for these situations, did not work.
        var list_view_table_nodes = dojo.query('.plant-list table');
        if (list_view_table_nodes.length > 0) {
            return;
        }

        var viewport = dijit.getViewport();
        var viewport_height = viewport.h;
        var scroll_top = 0;
        var scroll_left = 0;

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

        var image_elements = dojo.query('div.plant-list img');
        var i;
        for (i = 0; i < image_elements.length; i += 1) {
            var element = image_elements[i];
            if (element.style.visibility !== 'hidden' &&
                element.style.display !== 'none') {

                var current_element = element;
                var total_offset_left = current_element.offsetLeft;
                var total_offset_top = current_element.offsetTop;

                while (current_element.offsetParent !== null) {
                    current_element = current_element.offsetParent;
                    total_offset_left += current_element.offsetLeft;
                    total_offset_top += current_element.offsetTop;
                }

                var is_element_visible = false;
                // Only worry about top/bottom scroll visibility, not also
                // left/right scroll visibility.
                if (total_offset_top > (scroll_top - element.height) &&
                    total_offset_top < (viewport_height + scroll_top)) {

                    is_element_visible = true;
                }

                if (is_element_visible === true) {
                    var image_url = dojo.attr(element, 'x-tmp-src');
                    if (image_url !== null) {
                        // Set the attribute that will make the image load.
                        dojo.attr(element, 'src', image_url);
                    }
                }
            }
        }
    }

});

/*
 * Manage everywhere on the page that we maintain a species count.
 */
dojo.declare('gobotany.sk.SpeciesCounts', null, {
    animation: null,

    constructor: function() {
        dojo.subscribe('/filters/query-result', this, '_update_counts');
    },

    _update_counts: function(args) {
        var count_str = String(args.species_list.length);
        dojo.query('.species-count').html(count_str);

        if (this.animation !== null)
            this.animation.stop();

        var span = dojo.query('.species-count-heading > span');
        this.animation = span.animateProperty({
            duration: 2000,
            properties: {
                backgroundColor: {
                    start: '#FF0',
                    end: '#F0F0C0'
                }
            }
        });
        this.animation.play();
    }
});

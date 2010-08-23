// UI code for the Simple Key results/filter page.

// Global declaration for JSLint (http://www.jslint.com/)
/*global console, dojo, dojox, gobotany */

dojo.provide('gobotany.sk.results');
dojo.require('dojox.data.JsonRestStore');
dojo.require('gobotany.filters');
dojo.require('dojo.html');
dojo.require('dojo.data.ItemFileWriteStore');
dojo.require('dijit.Dialog');
dojo.require('dijit.form.Button');
dojo.require("dijit.form.FilteringSelect");
dojo.require('dijit.form.Form');
dojo.require('dijit.form.Select');

var filter_manager = null;
gobotany.sk.results.PAGE_COUNT = 12;
var scroll_event_handle = null;

// Name of the currently shown filter.
// TODO: perhaps move this into a function call that pulls this based on CSS
// property that indicates it's being shown
var simplekey_character_short_name = null;

// Image info storage for images that appear on the plant preview dialog box.
gobotany.sk.results.plant_preview_images = [];

gobotany.sk.results.show_filter_working = function(event) {
    event.preventDefault();

    // Here the 'this.' is a filter object passed in as a context.

    dojo.query('#filter-working').style({display: 'block'});
    dojo.query('#filter-working .name')[0].innerHTML = this.friendly_name;

    simplekey_character_short_name = this.character_short_name;

    var valuesList = dojo.query('#filter-working form .values')[0];
    dojo.empty(valuesList);
    if (this.value_type == 'LENGTH') {
        var range = this.values[0];
        dojo.place('<label>Type an integer value:<br>' +
                   '(hint: between ' + range.min + ' and ' +
                   range.max + ')<br>' +
                   '<input type="text" id="int_value" name="int_value"' +
                   ' value=""></label>',
                   valuesList);
    } else {
        dojo.place('<label><input type="radio" name="char_name" value="" ' +
                   'checked> don&apos;t know</label>', valuesList);
        for (var i = 0; i < this.values.length; i++) {
            var v = this.values[i];
            dojo.place('<label><input type="radio" name="char_name" ' +
                       'value="' + v.value + '"> ' + v.value +
                       ' (' + v.count + ')</label>', valuesList);
        }
    }

    var kc = dojo.query('#filter-working .info .key-characteristics')[0];
    kc.innerHTML = this.key_characteristics;

    var ne = dojo.query('#filter-working .info .notable-exceptions')[0];
    ne.innerHTML = this.notable_exceptions;

    // If the user has already selected a value for this filter, we
    // pre-check that radio button, instead of pre-checking the first
    // (the "Don't know") radio button like we normally do.

    var selector = '#filter-working .values input';
    var already_selected_value = filter_manager.get_selected_value(
        this.character_short_name);
    if (already_selected_value) {
        selector = selector + '[value="' + already_selected_value + '"]';
    }
    dojo.query(selector)[0].checked = true;
};

gobotany.sk.results.hide_filter_working = function() {
    dojo.query('#filter-working').style({display: 'none'});
    simplekey_character_short_name = null;
};

gobotany.sk.results.clear_filter = function(event) {
    event.preventDefault();

    if (this.character_short_name == simplekey_character_short_name) {
        gobotany.sk.results.hide_filter_working();
    }

    if (filter_manager.get_selected_value(this.character_short_name)) {
        filter_manager.set_selected_value(this.character_short_name, null);
        gobotany.sk.results.run_filtered_query();
    }

    dojo.query('#' + this.character_short_name + ' .choice'
              )[0].innerHTML = 'don\'t know';
};

gobotany.sk.results.remove_filter = function(event) {
    event.preventDefault();

    if (this.character_short_name == simplekey_character_short_name) {
        gobotany.sk.results.hide_filter_working();
    }

    if (filter_manager.get_selected_value(this.character_short_name)) {
        filter_manager.set_selected_value(this.character_short_name, null);
        gobotany.sk.results.run_filtered_query();
    }

    dojo.query('#' + this.character_short_name).orphan();
};

gobotany.sk.results.setup_filters = function(args) {
    var filtersList = dojo.query('#filters ul')[0];

    var first = null;
    if (!args.add)
        dojo.empty(filtersList);
    else {
        var lis = dojo.query('li', filtersList);
        if (lis.length > 0)
            first = lis[0];
    }
        
    
    
    var filters = args.filters;
    var added = [];
    for (var i = 0; i < filters.length; i++) {
        var filter = filters[i];
        if (filter.value_type != null) {
            var filterLink = dojo.create('a', {
                href: '#', innerHTML: filter.friendly_name});
            var choiceDiv = dojo.create('div', {
                'class': 'choice', innerHTML: 'don\'t know'});
            var removeLink = dojo.create('a', {
                href: '#', innerHTML: '× remove'});
            var clearLink = dojo.create('a', {
                href: '#', innerHTML: '× clear'});

            // Pass the filter to the function as its context (this).
            dojo.connect(filterLink, 'onclick', filter,
                         gobotany.sk.results.show_filter_working);
            dojo.connect(removeLink, 'onclick', filter,
                         gobotany.sk.results.remove_filter);
            dojo.connect(clearLink, 'onclick', filter,
                         gobotany.sk.results.clear_filter);

            var filterItem = dojo.create('li', 
                                         {id: filter.character_short_name});
            dojo.place(filterLink, filterItem);
            dojo.place(choiceDiv, filterItem);
            dojo.place(removeLink, filterItem);
            dojo.place(clearLink, filterItem);

            if (first) {
                dojo.place(filterItem, first, 'before');
                dojo.style(filterItem, {backgroundColor: '#FFF8DC'});
                added.push(filterItem);
            } else
                dojo.place(filterItem, filtersList);

        }

        if (added.length > 0) {
            setTimeout(function() {
                for (var x = 0; x < added.length; x++)
                    dojo.anim(added[x], {backgroundColor: 'white'});
            }, 2000);
        }
    }
};

gobotany.sk.results.apply_filter = function(event) {
    event.preventDefault();

    var choice_div = dojo.query('#' + simplekey_character_short_name +
                                ' .choice')[0];

    // First, see if this is a numeric field.

    var char_value_q = dojo.query('#character_values_form #int_value');

    if (char_value_q.length) {
        var value = parseInt(char_value_q[0].value, 10);
        if (!isNaN(value)) {
            filter_manager.set_selected_value(simplekey_character_short_name, 
                                              value);
            choice_div.innerHTML = value;
            gobotany.sk.results.run_filtered_query();
        }
        return;
    }

    // Next, look for a traditional checked multiple-choice field.

    var checked_item_q = dojo.query('#character_values_form input:checked');

    if (checked_item_q.length) {
        var checked_item = checked_item_q[0];
        filter_manager.set_selected_value(simplekey_character_short_name, 
                                          checked_item.value);
        if (checked_item.value) {
            choice_div.innerHTML = checked_item.value;
        } else {
            choice_div.innerHTML = 'don\'t know';
        }
        gobotany.sk.results.run_filtered_query();
        return;
    }

    // Well, drat.

    console.log('"Apply" button pressed, but no widget found');
};

gobotany.sk.results.run_filtered_query = function() {
    // Unbind the prior scroll event handler
    if (scroll_event_handle) {
        dojo.disconnect(scroll_event_handle);
    }
    dojo.empty('plant-listing');
    dojo.query('#plants .species_count .loading').removeClass('hidden');
    dojo.query('#plants .species_count .count').addClass('hidden');

    // Run the query, passing a callback function to be run when finished.
    filter_manager.run_filtered_query(
        gobotany.sk.results.on_complete_run_filtered_query);
};

gobotany.sk.results.change_plant_preview_image = function(event) {
    event.preventDefault();
    //alert('this.innerHTML: ' + this.innerHTML);
    var img = dojo.query('#plant-preview .photos img')[0];
    var current_image_url = dojo.attr(img, 'src');
    
    var current_image_index = null;
    var i = 0;
    while (current_image_index === null &&
           i < gobotany.sk.results.plant_preview_images.length) {
        if (current_image_url ===
            gobotany.sk.results.plant_preview_images[i].scaled_url) {

            current_image_index = i;
        }
        i++;
    }
    
    // Figure out which image to show next.
    var new_image_index = current_image_index;
    if (this.innerHTML.indexOf('next') >= 0) {
        new_image_index++;
    }
    else if (this.innerHTML.indexOf('prev') >= 0) {
        new_image_index--;
    }
    if (new_image_index < 0) {
        new_image_index =
            gobotany.sk.results.plant_preview_images.length - 1;
    }
    else if (new_image_index >
             gobotany.sk.results.plant_preview_images.length - 1) {
        new_image_index = 0;
    }
    
    // Change the image.
    dojo.attr(img, 'src', gobotany.sk.results.plant_preview_images[
                          new_image_index].scaled_url);
    dojo.attr(img, 'alt', gobotany.sk.results.plant_preview_images[
                          new_image_index].title);
    // Update the position/count message.
    var msg = dojo.query('#plant-preview .photos span')[0];
    msg.innerHTML = (new_image_index + 1) + ' of ' +
        gobotany.sk.results.plant_preview_images.length;
};

gobotany.sk.results.show_plant_preview = function(event) {
    event.preventDefault();
    var plant = this;   // Plant item passed as the context
    dijit.byId('plant-preview').show();
    dojo.query('#plant-preview h3')[0].innerHTML = '<i>' +
        plant.scientific_name + '</i>';
    var list = dojo.query('#plant-preview dl')[0];
    dojo.empty(list);

    var taxon_store = new dojox.data.JsonRestStore(
        {target: '/taxon/' + plant.scientific_name});
    taxon_store.fetch({
        onComplete: function(taxon) {
            for (var i = 0;
                 i < filter_manager.plant_preview_characters.length; i++) {
                var ppc = filter_manager.plant_preview_characters[i];
                dojo.create('dt', {innerHTML: ppc.character_friendly_name},
                            list);
                dojo.create('dd', 
                            {innerHTML: taxon[ppc.character_short_name]},
                            list);
            }
            dojo.create('dt', {innerHTML: 'Collection'}, list);
            var piles = '';
            for (var i = 0; i < taxon.piles.length; i++) {
                if (i > 0) {
                    piles += ', ';
                }
                piles += taxon.piles[i];
            }
            dojo.create('dd', {innerHTML: piles}, list);
            
            // Clear the images area.
            var img = dojo.query('#plant-preview .photos img')[0];
            dojo.attr(img, 'src', '');
            dojo.attr(img, 'alt', 'image not available');
            var msg = dojo.query('#plant-preview .photos span')[0];
            msg.innerHTML = '';
            
            gobotany.sk.results.plant_preview_images = [];
            if (taxon.images.length) {
                // Store the info for the images to allow for browsing them.
                for (var i = 0; i < taxon.images.length; i++) {
                    gobotany.sk.results.plant_preview_images.push(
                        taxon.images[i]);
                }
                // Set the first image.
                dojo.attr(img, 'src', 
                    gobotany.sk.results.plant_preview_images[0].scaled_url);
                // TODO: is this title field intended/sufficient for alt text?
                dojo.attr(img, 'alt',
                    gobotany.sk.results.plant_preview_images[0].title);
                // Set the count message.
                msg.innerHTML = '1 of ' + taxon.images.length;
            }
            // Wire up the previous and next links, or hide them if
            // they're not needed.
            var links = dojo.query('#plant-preview .photos a');
            for (var i = 0; i < links.length; i++) {
                if (taxon.images.length > 1) {
                    dojo.removeClass(links[i], 'hidden');
                    dojo.connect(links[i], 'onclick',
                        gobotany.sk.results.change_plant_preview_image);
                }
                else {
                    dojo.addClass(links[i], 'hidden');
                }
            }
         }
    });
};

gobotany.sk.results.paginate_results = function(items, start) {
    var page
    var page_num;
    var list;
    dojo.forEach(items, 
                 function (item, i) {
                     var remainder = i%gobotany.sk.results.PAGE_COUNT;
                     if (remainder == 0) {
                         page_num = ((i-remainder)/gobotany.sk.results.PAGE_COUNT) + 1;
                         page = dojo.create('li', {'class': 'PlantScrollPage',
                                                   id: 'plant-page-'+page_num.toString()},
                                            start);
                         dojo.html.set(page, 'Page ' + page_num.toString());
                         list = dojo.create('ul', {}, page);
                         // All items on the first page have been loaded
                         dojo.attr(page, 'x-loaded', page_num == 1 ? 'true': 'false');
                         
                     }
                     gobotany.sk.results.render_item(item, list, 
                                                          partial=(page_num!=1));
                 });
    return start;
}

gobotany.sk.results.render_item = function(item, start_node, partial) {
    // Fill in the search list with anchors, images and titles
    var li_node = dojo.create('li', 
                           {'id': 'plant-'+item.scientific_name.toLowerCase().replace(/\W/,'-')},
                           start_node
                          );
    dojo.connect(li_node, 'onclick', item, gobotany.sk.results.show_plant_preview);
    var anchor = dojo.create('a', {href: '#'}, li_node);
    var image = item.default_image;
    if (image) {
        var img = dojo.create('img', {height: image.thumb_height, 
                                      width: image.thumb_width, 
                                      alt: image.title,
                                      'x-plant-id': item.scientific_name},
                    anchor);
        // If a partial rendering was requested set a secret attribute instead of src
        // We can use that to fill src when scrolling
        var img_attr = partial ? 'x-tmp-src' : 'src';
        dojo.attr(img, img_attr, image.thumb_url);
        dojo.style(img, 'height', image.thumb_height);
    } else {
        dojo.create('span', {'class': 'MissingImage'},anchor);
    }
    var title = dojo.create('span', {'class': 'PlantTitle'}, anchor);
    dojo.html.set(title, item.scientific_name);
}

gobotany.sk.results.load_page = function(page) {
    var images = dojo.query('img[src=]', page);
    images.forEach(function (image, i) {
                       dojo.attr(image, 'src', dojo.attr(image, 'x-tmp-src'));
                   });
    dojo.attr(page, 'x-loaded', 'true');
}

gobotany.sk.results.load_page_if_visible = function(page) {
    // Don't load a page if it's already loaded
    if (dojo.attr(page, 'x-loaded') == 'true') { return; };
    // Check to see if the page is inside the parent viewport
    var container_pos = dojo.position(dojo.byId('plants'), false);
    var page_pos = dojo.position(page, false).y;
    if (container_pos.h >= (page_pos - container_pos.y)) {
            gobotany.sk.results.load_page(page);
    }
}

gobotany.sk.results.rebuild_family_select = function(items) {

    // Does sort | uniq really have to be this painful in JavaScript?

    var families_seen = {};
    var family_list = [];

    for (var i=0; i < items.length; i++) {
        var item = items[i];
        if (! families_seen[item.family]) {
            family_list.push(item.family);
            families_seen[item.family] = true;
        }
    }

    family_list.sort();

    // Update the Family data store.

    var family_store = dijit.byId('family_select').store;

    family_store.fetch({onComplete: function (items) {
        for (var i=0; i < items.length; i++)
            family_store.deleteItem(items[i]);
        family_store.save();
        for (var i=0; i < family_list.length; i++) {
            var f = family_list[i];
            family_store.newItem({ name: f, family: f });
        }
        family_store.save();
    }});
}

gobotany.sk.results.rebuild_genus_select = function(items) {

    genus_to_family = {};  // global, for use in another function below

    // Does sort | uniq really have to be this painful in JavaScript?

    var genera_seen = {};
    var genus_list = [];

    for (var i=0; i < items.length; i++) {
        var item = items[i];
        if (! genera_seen[item.genus]) {
            genus_list.push(item.genus);
            genera_seen[item.genus] = true;
            genus_to_family[item.genus] = item.family;
        }
    }

    genus_list.sort();

    // Update the Genus data store.

    var genus_store = dijit.byId('genus_select').store;

    genus_store.fetch({onComplete: function (items) {
        for (var i=0; i < items.length; i++)
            genus_store.deleteItem(items[i]);
        genus_store.save();
        for (var i=0; i < genus_list.length; i++) {
            var g = genus_list[i];
            genus_store.newItem({ name: g, genus: g });
        }
        genus_store.save();
    }});
}

gobotany.sk.results.narrow_by_family = function(items) {
    var family = dijit.byId('family_select').value;
    if (family)
        for (var i = items.length - 1; i > 0; i--)
            if (items[i].family != family)
                items.splice(i, 1);
}

gobotany.sk.results.narrow_by_genus = function(items) {
    var genus = dijit.byId('genus_select').value;
    if (genus)
        for (var i = items.length - 1; i >= 0; i--)
            if (items[i].genus != genus)
                items.splice(i, 1);
}

gobotany.sk.results.on_complete_run_filtered_query = function(data) {

    // Getting the "Family" and "Genus" boxes properly populated is a
    // bit tricky, because simply using them as normal parameters in our
    // big query would, for example, empty out the "Family" drop-downs
    // of every family except the one you had just selected!
    //
    // So, we do our "big query" *without* any restriction on family and
    // genus, so that we can populate the family field with all of its
    // options for the current filters, then we narrow the list of items
    // "by hand" so that the rest of the display logic can only see the
    // results for the currently-selected family.

    gobotany.sk.results.rebuild_family_select(data.items);
    gobotany.sk.results.narrow_by_family(data.items);
    gobotany.sk.results.rebuild_genus_select(data.items);
    gobotany.sk.results.narrow_by_genus(data.items);

    // Update the species count on the screen.
    dojo.query('#plants .species_count .count .number')[0].innerHTML =
        data.items.length;
    dojo.query('#plants .species_count .loading').addClass('hidden');
    dojo.query('#plants .species_count .count').removeClass('hidden');

    // Clear display
    var plant_listing = dojo.byId('plant-listing');
    gobotany.sk.results.paginate_results(data.items, plant_listing);

    // Define the pages here to make the event handler a bit more efficient
    // Bind a handler to load images on scroll
    var plant_scrollable = dojo.byId('plants');
    var plant_pages = dojo.query('li.PlantScrollPage[x-loaded=false]', plant_listing);
    scroll_event_handle = dojo.connect(plant_scrollable, 'onscroll',
                                       function () {
                                           plant_pages.forEach(gobotany.sk.results.load_page_if_visible);
                                       });
    dojo.publish("results_loaded", [{filter_manager: filter_manager,
                                    data: data}]);
};

did_they_just_choose_a_genus = false;

gobotany.sk.results.apply_family_filter = function(event) {
    if (! did_they_just_choose_a_genus)
        dijit.byId('genus_select').set('value', '');
    gobotany.sk.results.run_filtered_query();
    did_they_just_choose_a_genus = false;
};

gobotany.sk.results.apply_genus_filter = function(event) {
    var genus = dijit.byId('genus_select').value;
    var family_select = dijit.byId('family_select');
    if (genus) {
        var family = family_select.value;
        var new_family = genus_to_family[genus];
        if (family != new_family) {
            did_they_just_choose_a_genus = true;
            family_select.set('value', new_family);
        } else {
            gobotany.sk.results.run_filtered_query();
        }
    } else {
        gobotany.sk.results.run_filtered_query();
    }
};

gobotany.sk.results.clear_family = function(event) {
    event.preventDefault();
    dijit.byId('family_select').set('value', '');
}

gobotany.sk.results.clear_genus = function(event) {
    event.preventDefault();
    dijit.byId('genus_select').set('value', '');
}

gobotany.sk.results.get_more_filters = function(event) {
    event.preventDefault();
    var button = dijit.byId('more_filters_button');
    button.set('disabled', true);
    filter_manager.query_best_filters({onLoaded: function(items) {
        gobotany.sk.results.setup_filters({filters: items, add: true});
        button.set('disabled', false);
    }});
};

gobotany.sk.results.init = function(pile_slug) {
    // Wire up the filter working area's close button.
    var el = dojo.query('#filter-working .close')[0];
    dojo.connect(el, 'onclick', null, 
                 gobotany.sk.results.hide_filter_working);

    // Wire up the Family and Genus submit buttons.
    var family_store = new dojo.data.ItemFileWriteStore(
        {data: { label: 'name', identifier: 'family', items: [] }});

    var genus_store = new dojo.data.ItemFileWriteStore(
        {data: { label: 'name', identifier: 'genus', items: [] }});

    var family_select = dijit.byId('family_select');
    family_select.set('required', false);
    family_select.set('store', family_store);
    dojo.connect(family_select, 'onChange', null,
                 gobotany.sk.results.apply_family_filter);

    var genus_select = dijit.byId('genus_select');
    genus_select.set('required', false);
    genus_select.set('store', genus_store);
    dojo.connect(genus_select, 'onChange', null,
                 gobotany.sk.results.apply_genus_filter);

    // Wire up the "Clear" buttons for the family and genus.
    dojo.connect(dojo.byId('clear_family'), 'onclick', null,
                 gobotany.sk.results.clear_family);
    dojo.connect(dojo.byId('clear_genus'), 'onclick', null,
                 gobotany.sk.results.clear_genus);

    // Wire up the "More filters" button.
    var form = dijit.byId('more_filters_form');
    dojo.connect(form, 'onSubmit', null,
                 gobotany.sk.results.get_more_filters);

    // Wire up the Apply button in the filter working area.
    var apply_button = dojo.query('#character_values_form button')[0];
    dojo.connect(apply_button, 'onclick', null,
                 gobotany.sk.results.apply_filter);

    // Create a FilterManager object, which will pull a list of default
    // filters for the pile.
    filter_manager = new gobotany.filters.FilterManager(
                         {pile_slug: pile_slug});
    gobotany.sk.results.refresh_default_filters();

    // We start with no filter values selected so we can run the query before they load
    gobotany.sk.results.run_filtered_query();
    
    dojo.subscribe("results_loaded", gobotany.sk.results.populate_image_types);

    // Update images on selction change
    var select_box = dojo.byId('image-type-selector');
    dojo.connect(select_box, 'change', 
                 gobotany.sk.results.load_selected_image_type);

};

gobotany.sk.results.add_character_groups = function(filter_manager) {
    var my_form = dojo.query('#more_filters form div')[0];
    for (i=0; i < filter_manager.character_groups.length; i++) {
        var character_group = filter_manager.character_groups[i];
        var my_label = dojo.create('label', {
            'for': character_group.name,
        }, my_form, 'last');
        dojo.create('input', {
            type: 'checkbox',
            name: character_group.name,
            value: character_group.name,
        }, my_label);
        my_label.innerHTML += character_group.name;
    }
}

gobotany.sk.results.refresh_default_filters = function() {
    dojo.query('#filters .loading').removeClass('hidden');
    filter_manager.load_default_filters({onLoaded: function() {

        // Set up the character group checkboxes.
        gobotany.sk.results.add_character_groups(filter_manager);
        console.log('character group checkboxes created');

        // Populate the initial list of default filters.
        gobotany.sk.results.setup_filters({filters: filter_manager.filters});
        console.log('default filters loaded and configured');

        // Add Family and Genus filters.
        filter_manager.add_text_filters(['family', 'genus']);
        dojo.query('#filters .loading').addClass('hidden');

    }});
};

// A subscriber for results_loaded
gobotany.sk.results.populate_image_types = function(message) {
    var results = message.data.items;
    var select_box = dijit.byId('image-type-selector');
    // clear the select
    select_box.options.length = 0;
    // image types depend on the pile, we get the allowed values from
    // the result set for now
    var image_types = new Array();
    for (var i=0; i < results.length; i++) {
        var images = results[i].images;
        for (var j=0; j < images.length; j++) {
            var image_type = images[j].type;
            if (image_types.indexOf(image_type) == -1) {
                image_types.push(image_type);
            }
        }
    }
    // sort lexicographically
    image_types.sort();
    for (i=0; i < image_types.length; i++) {
        var image_type = image_types[i];
        select_box.options[i] = new Option(image_type, 
                                           image_type);
        // Habit is selected by default
        if (image_type == 'habit') {
            select_box.options[i].selected = true;
        }
    }
}

gobotany.sk.results.load_selected_image_type = function (event) {
    var image_type = dojo.byId('image-type-selector').value;
    var images = dojo.query('#plant-listing li img');
    // Replace the image for each plant on the page
    for (var i=0; i < images.length; i++) {
        var image = images[i];
        // Fetch the species for the current image
        filter_manager.result_store.fetchItemByIdentity({
               scope: {image: image,
                       image_type: image_type},
               identity: dojo.attr(image, 'x-plant-id'),
               onItem: function(item) {
                   var new_image;
                   // Search for an image of the correct type
                   for (var j=0; j < item.images.length; j++) {
                       if (item.images[j].type == image_type) {
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
                       var src_var = dojo.attr(image, 'x-tmp-src') ? 'x-tmp-src' : 'src';
                       dojo.attr(image, src_var, new_image.thumb_url);
                       // Hide the empty box if it exists and make
                       // sure the image is visible.
                       dojo.query('+ span.MissingImage', image).orphan();
                       dojo.style(image, 'display', 'inline');
                   } else if (dojo.style(image, 'display') != 'none') {
                       // If there's no matching image display the
                       // empty box and hide the image
                       dojo.style(image, 'display', 'none');
                       dojo.create('span', {'class': 'MissingImage'}, image, 'after');
                   }
               }
        });
    }
}

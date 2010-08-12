// UI code for the Simple Key results/filter page.

// Global declaration for JSLint (http://www.jslint.com/)
/*global console, dojo, dojox, gobotany */

dojo.provide('gobotany.sk.results');
dojo.require('dojox.data.JsonRestStore');
dojo.require('gobotany.filters');
dojo.require('dojo.html');

var filter_manager = null;

// Name of the currently shown filter.
// TODO: perhaps move this into a function call that pulls this based on CSS
// property that indicates it's being shown
var simplekey_character_short_name = null;

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

    // TODO: Check the user's chosen item if this filter is "active."
    // (For now, just check Don't Know.)
    dojo.query('#filter-working .values input')[0].checked = true;
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

gobotany.sk.results.populate_default_filters = function(filter_manager) {
    var filtersList = dojo.query('#filters ul')[0];
    dojo.empty(filtersList);
    
    for (var i = 0; i < filter_manager.filters.length; i++) {
        var filter = filter_manager.filters[i];
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

            dojo.place(filterItem, filtersList);
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
    dojo.empty('plant-listing');
    dojo.query('#plants .species_count .loading').removeClass('hidden');
    dojo.query('#plants .species_count .count').addClass('hidden');

    // Run the query, passing a callback function to be run when finished.
    filter_manager.run_filtered_query(
        gobotany.sk.results.on_complete_run_filtered_query);
};

gobotany.sk.results.on_complete_run_filtered_query = function(data) {
    // Update the species count on the screen.
    dojo.query('#plants .species_count .count .number')[0].innerHTML =
        filter_manager.species_count.toString();
    dojo.query('#plants .species_count .loading').addClass('hidden');
    dojo.query('#plants .species_count .count').removeClass('hidden');
    var plant_listing = dojo.byId('plant-listing');
    dojo.forEach(data.items, 
                 function (item, i) {
                     // Fill in the search list with anchors, images and titles
                     var node = dojo.create('li', 
                                            {'id': 'plant-'+item.scientific_name.toLowerCase().replace(/\W/,'-')},
                                            plant_listing
                                           );
                     var anchor = dojo.create('a', {href: '#'}, node);
                     var image = item.default_image;
                     if (image) {
                         dojo.create('img', {src: image.thumb_url, 
                                             height: image.thumb_height, 
                                             width: image.thumb_width, 
                                             alt: image.title},
                                     anchor);
                     } else {
                         dojo.create('span', {'class': 'MissingImage'},anchor);
                     }
                     var title = dojo.create('span', {'class': 'PlantTitle'}, anchor);
                     dojo.html.set(title, item.scientific_name);
                 });
};

gobotany.sk.results.apply_family_filter = function(event) {
    event.preventDefault();

    var family = dojo.query('#family_form input')[0].value;
    filter_manager.set_selected_value('family', family);

    gobotany.sk.results.run_filtered_query();
};

gobotany.sk.results.apply_genus_filter = function(event) {
    event.preventDefault();

    var genus = dojo.query('#genus_form input')[0].value;
    filter_manager.set_selected_value('genus', genus);

    gobotany.sk.results.run_filtered_query();
};

gobotany.sk.results.init = function(pile_slug) {
    // Wire up the filter working area's close button.
    var el = dojo.query('#filter-working .close')[0];
    dojo.connect(el, 'onclick', null, 
                 gobotany.sk.results.hide_filter_working);

    // Wire up the Family and Genus submit buttons.
    var family_button = dojo.query('#family_form button')[0];
    dojo.connect(family_button, 'onclick', null,
                 gobotany.sk.results.apply_family_filter);

    var genus_button = dojo.query('#genus_form button')[0];
    dojo.connect(genus_button, 'onclick', null,
                 gobotany.sk.results.apply_genus_filter);

    // Wire up the "Apply" button.
    var apply_button = dojo.query('#character_values_form button')[0];
    dojo.connect(apply_button, 'onclick', null,
                 gobotany.sk.results.apply_filter);

    // Create a FilterManager object, which will pull a list of default
    // filters for the pile.
    filter_manager = new gobotany.filters.FilterManager(
                         {pile_slug: pile_slug});
    filter_manager.load_default_filters({onLoaded: function() {
        // Populate the initial list of default filters.
        gobotany.sk.results.populate_default_filters(filter_manager);
        console.log('default filters loaded and configured');

        // Add Family and Genus filters.
        filter_manager.add_text_filters(['family', 'genus']);
    }});
    // We start with no filter values selected so we can run the query before they load
    gobotany.sk.results.run_filtered_query();

};

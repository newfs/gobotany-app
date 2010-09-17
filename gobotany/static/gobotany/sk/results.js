// UI code for the Simple Key results/filter page.

// Global declaration for JSLint (http://www.jslint.com/)
/*global console, dojo, dojox, gobotany */

dojo.provide('gobotany.sk.results');

dojo.require('gobotany.sk.plant_preview');
dojo.require('gobotany.filters');
dojo.require('gobotany.piles');
dojo.require('gobotany.utils');

dojo.require('dojo.cookie');
dojo.require('dojo.hash');
dojo.require('dojo.html');
dojo.require('dojo.data.ItemFileWriteStore');
dojo.require('dijit.Dialog');
dojo.require('dijit.form.Button');
dojo.require('dijit.form.CheckBox');
dojo.require("dijit.form.FilteringSelect");
dojo.require('dijit.form.Form');
dojo.require('dijit.form.HorizontalSlider');
dojo.require("dijit.form.HorizontalRuleLabels");
dojo.require('dijit.form.Select');

var filter_manager = null;
gobotany.sk.results.PAGE_COUNT = 12;
var scroll_event_handle = null;

// Name of the currently shown filter.
// TODO: perhaps move this into a function call that pulls this based on CSS
// property that indicates it's being shown
var simplekey_character_short_name = null;

dojo.declare('gobotany.sk.results.ResultsHelper', null, {
    constructor: function(pile_slug) {
        this.pile_slug = pile_slug 
        this.pile_manager = new gobotany.piles.PileManager(this.pile_slug);
   },

    setup: function() {
        console.log('ResultsHelper: setting up page - '+this.pile_slug);
        gobotany.sk.results.init(this.pile_slug);

        // for now the init() function below sets up the much needed filter_manager obj
        this.filter_manager = filter_manager;

        // whenever a filter value has changed, keep track of it in the url/cookie
        var track = dojo.hitch(this, this._track_filter_setting);
        dojo.connect(this.filter_manager, 'on_filter_changed', track);
        dojo.connect(this.filter_manager, 'on_filter_added', track);
        dojo.connect(this.filter_manager, 'on_filter_removed', track);

        this.filter_section = new gobotany.sk.results.FilterSectionHelper(this.filter_manager);
        this.filter_section.setup_section();

        dojo.connect(this.pile_manager, 'on_pile_info_changed', dojo.hitch(this, function(pile_info) {
            // a hash means filter state has been set, don't load up the default filters for a pile if
            // filter state has already been set

            var hash = dojo.hash();
            if (hash) {
                this._restore_filters(hash)
            } else {
                var filters = [];
                for (var x = 0; x < pile_info.default_filters.length; x++) {
                    var obj = pile_info.default_filters[x];
                    obj.pile_slug = this.pile_slug;
                    var filter = gobotany.filters.filter_factory(pile_info.default_filters[x]);
                    filters.push(filter);
                }
                var watcher = new gobotany.filters.FilterLoadingWatcher(filters);
                watcher.load_values({on_values_loaded: dojo.hitch(this, function(filters) { 
                    dojo.query('#filters .loading').addClass('hidden');
                    this.filter_section.display_filters(filters);
                })});
            }

            gobotany.sk.results.run_filtered_query();
        }));
        this.pile_manager.load();
    },

    _track_filter_setting: function() {
        console.log('saving filter info in url and cookie');
        dojo.hash(this.filter_manager.as_query_string());
        dojo.cookie('last_plant_id_url', window.location.href, {path: '/'});
    },

    _restore_filters: function(hash) {
        var filter_names = [];
        var hash_object = dojo.queryToObject(hash);
        console.log('family='+hash_object.family);
        if (hash_object['_filters'] === undefined)
            return;

        this.filter_manager.empty_filters();
        gobotany.sk.results.add_special_filters();

        var comma = hash_object['_filters'].split(',');
        var filter_values = [];
        for (var x = 0; x < comma.length; x++) {
            filter_values[comma[x]] = hash_object[comma[x]];
            if (this.filter_manager.has_filter(comma[x]))
                continue

            filter_names.push(comma[x]);
        }

        // Get all the filters from the server, passing a callback function
        // that will restore the filter values when done.
        this._get_url_filters(
            filter_names,
            dojo.hitch(this, function() {
                this._restore_filter_values(filter_values);
            }));

        dojo.query('#filters .loading').addClass('hidden');
    },

    _restore_filter_values: function(hash_object) {
        for (var filter in hash_object) {
            if (hash_object.hasOwnProperty(filter)) {
                if (hash_object[filter] !== undefined && hash_object[filter].length) {
                    filter_manager.set_selected_value(filter,
                                                      hash_object[filter]);
                    if (filter == 'family')
                        dijit.byId('family_select').set('value', hash_object.family);
                    else if (filter == 'genus')
                        dijit.byId('genus_select').set('value', hash_object.genus);
                    else {
                        var choice_div = dojo.query('#' + filter + ' .choice')[0];
                        choice_div.innerHTML = hash_object[filter];
                    }
                }
            }
        }
        
        // Now that the values are restored, run the query to update.
        gobotany.sk.results.run_filtered_query();
    },

    _get_url_filters: function(short_names, callback) {
        // Get and add filters that were present on the URL when the page was
        // loaded. (This is done instead of adding default filters.)

        this.filter_manager.query_filters({
            short_names: short_names,
            onLoaded: dojo.hitch(this, function(items) {
                if (items.length > 0) {
                    this.filter_section.display_filters(items);
                    // Call the callback function passed in, in order to
                    // continue when completed.
                    callback();
                }
            })
        });
    }

});

dojo.declare('gobotany.sk.results.FilterSectionHelper', null, {
    constructor: function(filter_manager) {
        this.filter_manager = filter_manager;
    },

    setup_section: function() {
        console.log('FilterSectionHelper: setting up section');
        dojo.connect(this.filter_manager, 'on_character_groups_changed',
                     dojo.hitch(this, this._setup_character_groups));

        // Wire up the "More filters" button.
        var form = dijit.byId('more_filters_form');
        dojo.connect(form, 'onSubmit', null,
                     dojo.hitch(this, this._get_more_filters));

        dojo.connect(this.filter_manager, 'on_default_filters_loaded',
                    dojo.hitch(this, this._setup_default_filters));

    },

    _setup_character_groups: function() {
        console.log('FilterSectionHelper: Updating char groups');
        var my_form = dojo.query('#more_filters form div')[0];
        var menu = dijit.byId('character_groups_menu');

        for (var i = 0; i < this.filter_manager.character_groups.length; i++) {
            var character_group = this.filter_manager.character_groups[i];
            var item = new dijit.CheckedMenuItem({label: character_group.name,
                                                  value: character_group.id});
            menu.addChild(item);
        }
    },

    _get_more_filters: function(event) {
        dojo.stopEvent(event);

        console.log('FilterSectionHelper: getting more filters...');

        var form = dijit.byId('more_filters_form');
        var button = dijit.byId('get_more_filters_button');
        button.set('disabled', true);
        
        var menu = dijit.byId('character_groups_menu');
        var character_group_ids = [];
        for (var x = 0; x < menu.getChildren().length; x++) {
            var item = menu.getChildren()[x];
            if (item.checked)
                character_group_ids.push(item.value);
        }

        var existing = [];
        for (var x = 0; x < this.filter_manager.filters.length; x++)
            existing.push(this.filter_manager.filters[x].character_short_name);
        this.filter_manager.query_best_filters({
            character_group_ids: character_group_ids,
            existing_characters: existing,
            onLoaded: dojo.hitch(this, function(items) {
                if (items.length > 0) {
                    var added = this.display_filters(items, 0);
                    added.style({backgroundColor: '#C8B560'});
                    gobotany.utils.notify('More filters added'); 
                    gobotany.utils.animate_changed(added);
                } else
                    gobotany.utils.notify('No filters left for the selected character groups');
                button.set('disabled', false);
            })
        });
    },

    _setup_default_filters: function() {
        dojo.query('#filters .loading').addClass('hidden');
        this.display_filters(filters);
    },

    display_filter: function(filter, idx) {
        var filter_ul = dojo.query('#filters ul')[0];
        var first = null;
        if (idx !== undefined) {
            var nodes = dojo.query('li', filter_ul);
            first = nodes[idx];
            if (first === undefined)
                first = nodes[nodes.length-1];
        }

        var filterItem = null;
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

            filterItem = dojo.create('li', 
                                     {id: filter.character_short_name});
            dojo.place(filterLink, filterItem);
            dojo.place(choiceDiv, filterItem);
            dojo.place(removeLink, filterItem);
            dojo.place(clearLink, filterItem);

            if (first != null) {
                dojo.place(filterItem, first, 'before');
                dojo.style(filterItem, {backgroundColor: '#C8B560'});
            } else {
                dojo.place(filterItem, filter_ul);
            }
        }

        return filterItem;
    },

    clear_filters: function() {
        dojo.query('#filters ul').empty();
    },

    display_filters: function(filters, idx) {
        var added = dojo.NodeList();
        for (var i = 0; i < filters.length; i++) {
            added.push(this.display_filter(filters[i], idx));
            if (idx !== undefined)
                idx++;
        }

        return added;
    }

});


gobotany.sk.results.init = function(pile_slug) {
    console.log('Init: initialization running');
    // Create a FilterManager object, which will pull a list of default
    // filters for the pile.
    filter_manager = new gobotany.filters.FilterManager({
        pile_slug: pile_slug
    });

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

    // Wire up the Apply button in the filter working area.
    var apply_button = dojo.query('#character_values_form button')[0];
    dojo.connect(apply_button, 'onclick', null,
                 gobotany.sk.results.apply_filter);

    dojo.subscribe("results_loaded", gobotany.sk.results.populate_image_types);

    // Update images on selction change
    var select_box = dojo.byId('image-type-selector');
    dojo.connect(select_box, 'change', 
                 gobotany.sk.results.load_selected_image_type);
};

// Update the filter working area "help text," which consists of the Key
// Characteristics and Notable Exceptions areas.
gobotany.sk.results.update_filter_working_help_text = function(event) {
    // Here the 'this.' is either a filter object or character value object
    // passed in as a context.
    
    var kc = dojo.query('#filter-working .info .key-characteristics')[0];
    kc.innerHTML = this.key_characteristics;

    var ne = dojo.query('#filter-working .info .notable-exceptions')[0];
    ne.innerHTML = this.notable_exceptions;
}

dojo.declare("gobotany.sk.results.UnitFieldsUpdater", null, {
    constructor: function(input1, input2, unit) {
        this.input1 = input1;
        this.input2 = input2;
        this.unit = unit;
        this.realvalue = null;
    },

    update_fields: function(value) {
        this.realvalue = value;
        var unit = this.unit;

        dojo.attr(this.input1, 'value', String(value.toFixed(2)) + unit);
        var valuemm = value;
        if (unit == 'cm')
            valuemm = 10 * valuemm;
        else if (unit == 'm')
            valuemm = 1000 * valuemm;

        var inches = 0.0393700787 * valuemm;
        var remaining = null;
        if (inches > 12) {
            var feet = inches / 12;
            feet = feet.toFixed(2);
            inches = inches % 12;
            inches = inches.toFixed(2);
            remaining = String(feet) + "'" + String(inches) + '"';
        } else {
            inches = inches.toFixed(2);
            remaining = String(inches) + '"'
        }

        dojo.attr(this.input2, 'value', remaining);
    }
});


gobotany.sk.results.show_filter_working = function(event) {
    dojo.stopEvent(event);

    // Here the 'this.' is a filter object passed in as a context.

    dojo.query('#filter-working').style({display: 'block'});
    dojo.query('#filter-working .name')[0].innerHTML = this.friendly_name;

    simplekey_character_short_name = this.character_short_name;

    var valuesList = dojo.query('#filter-working form .values')[0];
    dojo.empty(valuesList);
    if (this.value_type == 'LENGTH') {

        // Create a slider with horizontal rules and labels.

        var themin = this.values.min;
        var themax = this.values.max;
        var startvalue = (themax + themin) / 2.0;

        var selectedvalue = filter_manager.get_selected_value(
            this.character_short_name);
        if (selectedvalue != null)
            startvalue = selectedvalue;

        var label = dojo.place('<label>Select a length between<br>' +
                               this.values.min + '&thinsp;' +
                               this.unit + ' and ' +
                               this.values.max + '&thinsp;' +
                               this.unit + '<br></label>',
                               valuesList);

        var input = dojo.create('input', {
            type: 'text',
            name: 'int_value',
            disabled: true
        }, label);
        dojo.addClass(input, 'filter_int');

        var input2 = dojo.create('input', {
            type: 'text',
            name: 'int2_value',
            disabled: true
        }, label);
        dojo.addClass(input2, 'filter_int2');

        var updater = new gobotany.sk.results.UnitFieldsUpdater(input, input2, this.unit);
        updater.update_fields(startvalue);


        var slider_node = dojo.create('div', null, valuesList);
        var unit = this.unit;
        var slider = new dijit.form.HorizontalSlider({
            name: "character_slider",
            showButtons: false,
            value: startvalue,
            minimum: themin,
            maximum: themax,
            discreteValues: themax - themin + 1,
            intermediateChanges: true,
            style: "width:200px;",
            onChange: dojo.hitch(updater, updater.update_fields),
        }, slider_node);
        
        var rule_node = dojo.create('div', null, slider.containerNode);
        var ruleticks = new dijit.form.HorizontalRule({
            container: "topDecoration",
            count: themax - themin + 1,
            style: "height:10px;"
        }, rule_node);
        
        var labels_node = dojo.create('div', null, slider.containerNode);
        var mylabels = [];
        for (i=themin; i <= themax; i++) {
            mylabels.push(String(i));
        }
        var rule_labels = new dijit.form.HorizontalRuleLabels({
            container: "bottomDecoration",
            count: themax - themin + 1,
            labels: mylabels,
            style: "height:1.5em;font-size:75%;color:gray;width:200px"
        }, labels_node);        

    } else {

        // Create the radio-button widget.

        // Create a Don't Know radio button item.
        var item_html = '<input type="radio" name="char_name" value="" ' +
                   'checked> don&apos;t know';
        var dont_know_item = dojo.create('label',
                                         {'innerHTML': item_html});
        // Connect this radio button item to a function that will set the
        // Key Characteristics and Notable Exceptions for this filter.
        // Here the *filter* is passed as the context.
        dojo.connect(dont_know_item, 'onclick', this,
                     gobotany.sk.results.update_filter_working_help_text);
        dojo.place(dont_know_item, valuesList);

        // Create radio button items for each character value.
        for (var i = 0; i < this.values.length; i++) {
            var v = this.values[i];
            var item_html = '<input type="radio" name="char_name" value="' +
                v.value + '"> ' + v.value + ' (' + v.count + ')';
            var character_value_item = dojo.create('label',
                                                   {'innerHTML': item_html});
            // Connect this character value radio button item to a function
            // that will set the Key Characteristics and Notable Exceptions for
            // this particular character value. Here the *character value*
            // is passed as the context.
            dojo.connect(character_value_item, 'onclick', v,
                         gobotany.sk.results.update_filter_working_help_text);
            dojo.place(character_value_item, valuesList);
        }

        // If the user has already selected a value for this filter, we
        // pre-check that radio button, instead of pre-checking the
        // first (the "Don't know") radio button like we normally do.

        var selector = '#filter-working .values input';
        var already_selected_value = filter_manager.get_selected_value(
            this.character_short_name);
        if (already_selected_value) {
            selector = selector + '[value="' + already_selected_value + '"]';
        }
        dojo.query(selector)[0].checked = true;
    }

    // Set the key characteristics and notable exceptions for the filter
    // (character). (Elsewhere these will be set for character values.)

    var kc = dojo.query('#filter-working .info .key-characteristics')[0];
    kc.innerHTML = this.key_characteristics;

    var ne = dojo.query('#filter-working .info .notable-exceptions')[0];
    ne.innerHTML = this.notable_exceptions;
};

gobotany.sk.results.hide_filter_working = function() {
    dojo.query('#filter-working').style({display: 'none'});
    simplekey_character_short_name = null;
};

gobotany.sk.results.clear_filter = function(event) {
    dojo.stopEvent(event);

    if (this.character_short_name == simplekey_character_short_name) {
        gobotany.sk.results.hide_filter_working();
    }

    if (filter_manager.get_selected_value(this.character_short_name)) {
        filter_manager.set_selected_value(this.character_short_name, undefined);
        gobotany.sk.results.run_filtered_query();
    }

    dojo.query('#' + this.character_short_name + ' .choice'
              )[0].innerHTML = 'don\'t know';
};

gobotany.sk.results.remove_filter = function(event) {
    dojo.stopEvent(event);

    if (this.character_short_name == simplekey_character_short_name) {
        gobotany.sk.results.hide_filter_working();
    }

    if (filter_manager.has_filter(this.character_short_name)) {
        filter_manager.remove_filter(this.character_short_name);
        gobotany.sk.results.run_filtered_query();
    }

    dojo.query('#' + this.character_short_name).orphan();
};

gobotany.sk.results.apply_filter = function(event) {
    dojo.stopEvent(event);

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

gobotany.sk.results.paginate_results = function(items, start) {
    var page
    var page_num;
    var list;
    var previous_genus = 'this string matches no actual genus';
    var genus_number = -1;  // incremented each time we reach a new genus
    for (i=0; i < items.length; i++) {
        item = items[i];
        if (item.genus != previous_genus) {
            genus_number ++;
            previous_genus = item.genus;
        }
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
        gobotany.sk.results.render_item(item, list, genus_number,
                                        partial=(page_num!=1));
    }
    return start;
}

gobotany.sk.results.render_item = function(item, start_node, genus_number,
                                           partial) {
    // Fill in the search list with anchors, images and titles
    var genus_colors = 4;  // alternate between two colors for genera
    var li_node = dojo.create('li', {
        'id': 'plant-'+item.scientific_name.toLowerCase().replace(/\W/,'-'),
        'class': 'genus' + (genus_number % genus_colors).toString(),
    }, start_node);
    dojo.connect(li_node, 'onclick', item, function(event) {
        event.preventDefault();
        dijit.byId('plant-preview').show();
        var plant = this;
        gobotany.sk.plant_preview.show_plant_preview(plant);
    });
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

    var family_select = dijit.byId('family_select');
    var family_store = family_select.store;

    family_store.fetch({onComplete: function (items) {
        for (var i=0; i < items.length; i++)
            family_store.deleteItem(items[i]);
        family_store.save();
        for (var i=0; i < family_list.length; i++) {
            var f = family_list[i];
            family_store.newItem({ name: f, family: f });
        }
        family_store.save();

        var v = filter_manager.get_selected_value('family');
        if (v)
            family_select.set('value', v);
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

    var genus_select = dijit.byId('genus_select');
    var genus_store = genus_select.store;

    genus_store.fetch({onComplete: function (items) {
        for (var i=0; i < items.length; i++)
            genus_store.deleteItem(items[i]);
        genus_store.save();
        for (var i=0; i < genus_list.length; i++) {
            var g = genus_list[i];
            genus_store.newItem({ name: g, genus: g });
        }
        genus_store.save();

        var v = filter_manager.get_selected_value('genus');
        if (v)
            genus_select.set('value', v);
    }});
}

gobotany.sk.results.on_complete_run_filtered_query = function(data) {

    gobotany.sk.results.rebuild_family_select(data.items);
    gobotany.sk.results.rebuild_genus_select(data.items);

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
    if (! did_they_just_choose_a_genus) {
        dijit.byId('genus_select').set('value', '');
    }
    
    var family_select = dijit.byId('family_select');
    var family = family_select.value;
    filter_manager.set_selected_value('family', family);
    
    gobotany.sk.results.run_filtered_query();
    did_they_just_choose_a_genus = false;
};

gobotany.sk.results.apply_genus_filter = function(event) {
    var genus = dijit.byId('genus_select').value;
    filter_manager.set_selected_value('genus', genus);
    
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
};

gobotany.sk.results.add_special_filters = function() {
    filter_manager.add_special_filter({
        character_short_name: 'family',
        filter_callback: function(filter, item) {
            if (!filter.selected_value)
                return true;
            return filter.selected_value == item.family;
        }
    });
    filter_manager.add_special_filter({
        character_short_name: 'genus',
        filter_callback: function(filter, item) {
            if (!filter.selected_value)
                return true;
            return filter.selected_value == item.genus;
        }
    });
};

gobotany.sk.results.refresh_default_filters = function() {
    dojo.query('#filters .loading').removeClass('hidden');
    filter_manager.empty_filters();
    gobotany.sk.results.add_special_filters();
    filter_manager.load_pile_info({load_default_filters: true});
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
};

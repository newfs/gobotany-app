// UI code for the Simple Key results/filter page.

// Global declaration for JSLint (http://www.jslint.com/)
/*global console, dojo, dojox, gobotany */

dojo.provide('gobotany.sk.results');
dojo.require('dojox.data.JsonRestStore');
dojo.require('gobotany.filters');

var simplekey_character_short_name = null;
var simplekey_filter_choices = null;
var simplekey_pile_slug = null;

gobotany.sk.results.show_filter_working = function(event) {
    event.preventDefault();

    // Here the 'this.' is a filter object passed in as a context.

    dojo.query('#filter-working').style({ display: 'block' });
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
    dojo.query('#filter-working').style({ display: 'none' });
    simplekey_character_short_name = null;
};

gobotany.sk.results.clear_filter = function(event) {
    event.preventDefault();

    if (this.character_short_name == simplekey_character_short_name) {
        gobotany.sk.results.hide_filter_working();
    }
    if (this.character_short_name in simplekey_filter_choices) {
        delete simplekey_filter_choices[this.character_short_name];
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
    if (this.character_short_name in simplekey_filter_choices) {
        delete simplekey_filter_choices[this.character_short_name];
        gobotany.sk.results.run_filtered_query();
    }
    dojo.query('#' + this.character_short_name).orphan();
};

gobotany.sk.results.populate_default_filters = function(filter_manager) {
    var filtersList = dojo.query('#filters ul')[0];
    dojo.empty(filtersList);
    
    for (var i = 0; i < filter_manager.default_filters.length; i++) {
        var filter = filter_manager.default_filters[i];
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

        var filterItem = dojo.create('li', {id: filter.character_short_name});
        dojo.place(filterLink, filterItem);
        dojo.place(choiceDiv, filterItem);
        dojo.place(removeLink, filterItem);
        dojo.place(clearLink, filterItem);

        dojo.place(filterItem, filtersList);
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
            simplekey_filter_choices[simplekey_character_short_name] = value;
            choice_div.innerHTML = value;
            gobotany.sk.results.run_filtered_query();
        }
        return;
    }

    // Next, look for a traditional checked multiple-choice field.

    var checked_item_q = dojo.query('#character_values_form input:checked');

    if (checked_item_q.length) {
        var checked_item = checked_item_q[0];
        if (checked_item.value) {
            choice_div.innerHTML = checked_item.value;
            simplekey_filter_choices[simplekey_character_short_name] =
                checked_item.value;
        } else {
            choice_div.innerHTML = 'don\'t know';
            if (simplekey_character_short_name in simplekey_filter_choices) {
                delete simplekey_filter_choices[simplekey_character_short_name];
            }
        }
        gobotany.sk.results.run_filtered_query();
        return;
    }

    // Well, drat.

    console.log('"Apply" button pressed, but no widget found');
};

gobotany.sk.results.run_filtered_query = function() {
    dojo.query('#plants .species_count .loading').style({display: 'block'});
    dojo.query('#plants .species_count .count').style({display: 'none'});

    var content = { pile: simplekey_pile_slug };

    for (var key in simplekey_filter_choices) {
        if (simplekey_filter_choices.hasOwnProperty(key)) {
            content[key] = simplekey_filter_choices[key];
        }
    }

    var store = new dojox.data.JsonRestStore({ target: '/taxon/' });
    store.fetch({
        query: content,
        onComplete: function(data) {
            dojo.query('#plants .species_count .count')[0].innerHTML =
                data.items.length.toString() + ' species';

            dojo.query('#plants .species_count .loading'
                      ).style({display: 'none'});
            dojo.query('#plants .species_count .count'
                      ).style({display: 'block'});
        },
        onError: function(error) {
            console.log('Taxon search encountered an error!');
        }
    });
};

gobotany.sk.results.apply_family_filter = function(event) {
    event.preventDefault();

    var family = dojo.query('#family_form input')[0].value;
    if (family.length > 0) {
        simplekey_filter_choices.family = family;
    } else {
        if (simplekey_filter_choices.family) {
            delete simplekey_filter_choices.family;
        }
    }

    gobotany.sk.results.run_filtered_query();
};

gobotany.sk.results.apply_genus_filter = function(event) {
    event.preventDefault();

    var genus = dojo.query('#genus_form input')[0].value;
    if (genus.length > 0) {
        simplekey_filter_choices.genus = genus;
    } else {
        if (simplekey_filter_choices.genus) {
            delete simplekey_filter_choices.genus;
        }
    }

    gobotany.sk.results.run_filtered_query();
};

gobotany.sk.results.init = function(pile_slug) {
    // Leave data around for further calls to the API.
    simplekey_pile_slug = pile_slug;
    simplekey_filter_choices = [];

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
    var filter_manager = new gobotany.filters.FilterManager(
	                         { pile_slug: pile_slug });
    filter_manager.load_default_filters();

    // Populate the initial list of default filters.
    gobotany.sk.results.populate_default_filters(filter_manager);

    // We start with no filter values selected.
    gobotany.sk.results.run_filtered_query();
};

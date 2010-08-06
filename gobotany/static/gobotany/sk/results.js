// UI code for the Simple Key results/filter page.

dojo.provide('gobotany.sk.results');
dojo.require('dojox.data.JsonRestStore');
dojo.require('gobotany.filters');

gobotany.sk.results.show_filter_working = function() {
    // Here the 'this.' is a filter object passed in as a context.

    dojo.query('#filter-working').style({display: 'block'});
    dojo.query('#filter-working .name')[0].innerHTML = this.friendly_name;

    simplekey_character_short_name = this.character_short_name;

    var valuesList = dojo.query('#filter-working form .values')[0];
    dojo.empty(valuesList);
    dojo.place('<label><input type="radio" name="char_name" value="" ' +
               'checked> don&apos;t know</label>', valuesList);
    for (var i = 0; i < this.values.length; i++) {
        dojo.place('<label><input type="radio" name="char_name" ' +
                   'value="' + this.values[i] + '"> ' + this.values[i] +
                   ' (0)</label>', valuesList);
    }

    // TODO: Check the user's chosen item if this filter is "active."
    // (For now, just check Don't Know.)
    dojo.query('#filter-working .values input')[0].checked = true;
}

gobotany.sk.results.hide_filter_working = function() {
    dojo.query('#filter-working').style({display: 'none'});
};

gobotany.sk.results.populate_default_filters = function(filter_manager) {
    var filtersList = dojo.query('#filters ul')[0];
    dojo.empty(filtersList);
    
    for (var i = 0; i < filter_manager.default_filters.length; i++) {
        var filter = filter_manager.default_filters[i];
        var filterLink = dojo.create('a', {
            href: '#', innerHTML: filter.friendly_name});
        var choiceDiv = dojo.create('div', {
            class: 'choice', innerHTML: 'don\'t know'})
        var removeLink = dojo.create('a', {
            href: '#', innerHTML: '× remove'});
        var clearLink = dojo.create('a', {
            href: '#', innerHTML: '× clear'});

        // Pass the filter to the function as its context (this).
        dojo.connect(filterLink, 'onclick', filter, 
                     gobotany.sk.results.show_filter_working);

        filterItem = dojo.create('li', {id: filter.character_short_name});
        dojo.place(filterLink, filterItem)
        dojo.place(choiceDiv, filterItem)
        dojo.place(removeLink, filterItem)
        dojo.place(clearLink, filterItem)

        dojo.place(filterItem, filtersList);
    }
};

gobotany.sk.results.apply_filter = function() {
    choice_div = dojo.query('#' + simplekey_character_short_name +
                            ' .choice')[0];
    checked_item = dojo.query('#character_values_form input:checked')[0];
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
};

gobotany.sk.results.run_filtered_query = function() {
    dojo.query('#plants .species_count .loading').style({display: 'block'});
    dojo.query('#plants .species_count .count').style({display: 'none'});

    var content = { pile: simplekey_pile_slug };

    for (var key in simplekey_filter_choices) {
        content[key] = simplekey_filter_choices[key];
    }

    var store = new dojox.data.JsonRestStore({target: '/taxon/'});
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

gobotany.sk.results.init = function(pile_slug) {
    // Leave data around for further calls to the API.
    simplekey_pile_slug = pile_slug;
    simplekey_filter_choices = [];

    // Wire up the filter working area's close button.
    var el = dojo.query('#filter-working .close')[0];
    dojo.connect(el, 'onclick', null, 
                 gobotany.sk.results.hide_filter_working);

    // Wire up the "Apply" button.
    var apply_button = dojo.query('#character_values_form button')[0];
    dojo.connect(apply_button, 'onclick', null,
                 gobotany.sk.results.apply_filter);

    // Create a FilterManager object, which will pull a list of default
    // filters for the pile.
    var filter_manager = new FilterManager({pile_slug: pile_slug});
    filter_manager.load_default_filters();

    // Populate the initial list of default filters.
    gobotany.sk.results.populate_default_filters(filter_manager);

    // We start with no filter values selected.
    gobotany.sk.results.run_filtered_query();
};

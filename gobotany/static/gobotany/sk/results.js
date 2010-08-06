// UI code for the Simple Key results/filter page.

dojo.provide('gobotany.sk.results');
dojo.require('dojox.data.JsonRestStore');
dojo.require('gobotany.filters');

gobotany.sk.results.show_filter_working = function(character_friendly_name,
                                                   character_short_name,
                                                   values) {
    dojo.query('#filter-working').style({display: 'block'});
    dojo.query('#filter-working .name')[0].innerHTML = character_friendly_name;

    var valuesList = dojo.query('#filter-working .values form')[0];
    dojo.empty(valuesList);
    dojo.place('<label><input type="radio" name="char_name" value="" ' +
               'checked> don&apos;t know</label>', valuesList);
    for (var i = 0; i < values.length; i++) {
        dojo.place('<label><input type="radio" name="char_name" ' +
                   'value="' + values[i] + '"> ' + values[i] + 
                   ' (0)</label>', valuesList);
    }

    // TODO: Check the user's chosen item if this filter is "active."
    // (For now, just check Don't Know.)
    dojo.query('#filter-working .values input')[0].checked = true;
};

gobotany.sk.results.hide_filter_working = function() {
    dojo.query('#filter-working').style({display: 'none'});
};

gobotany.sk.results.populate_default_filters = function(filter_manager) {
    var filtersList = dojo.query('#filters ul')[0];
    dojo.empty(filtersList);
    
    for (var i = 0; i < filter_manager.default_filters.length; i++) {
        var filter = filter_manager.default_filters[i];
        filter_values = '[';
        for (var j = 0; j < filter.values.length; j++) {
            if (j !== 0) {
                filter_values += ', ';
            }
            filter_values += '\'' + filter.values[j] + '\'';
        }
        filter_values += ']';
        dojo.place('<li><a href="javascript:gobotany.sk.results.' +
                   'show_filter_working(\'' +
                   filter.friendly_name + '\', \'' + 
                   filter.character_short_name + '\', ' +
                   filter_values + ')">' +
                   filter.friendly_name +
                   '</a></li>', filtersList);
    }
};

gobotany.sk.results.init = function(pile_slug) {
    // Wire up the filter working area's close button.
    var el = dojo.query('#filter-working .close')[0];
    dojo.connect(el, 'onclick', null, 
                 gobotany.sk.results.hide_filter_working);

    // Create a FilterManager object, which will pull a list of default
    // filters for the pile.
    var filter_manager = new FilterManager({pile_slug: pile_slug});
    filter_manager.load_default_filters();

    // Populate the initial list of default filters.
    gobotany.sk.results.populate_default_filters(filter_manager);
};

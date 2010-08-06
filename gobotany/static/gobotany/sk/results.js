// UI code for the Simple Key results/filter page.

dojo.provide('gobotany.sk.results');
dojo.require('dojox.data.JsonRestStore');
dojo.require('gobotany.filters');

gobotany.sk.results.show_filter_working = function() {
    // Here the 'this.' is a filter object passed in as a context.

    dojo.query('#filter-working').style({display: 'block'});
    dojo.query('#filter-working .name')[0].innerHTML = this.friendly_name;

    var valuesList = dojo.query('#filter-working .values form')[0];
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
        var filterLink = dojo.create('a', {innerHTML: '<li><a href="#">' + 
                         filter.friendly_name + '</a></li>'});
        // Pass the filter to the function as its context (this).
        dojo.connect(filterLink, 'onclick', filter, 
                     gobotany.sk.results.show_filter_working);
        dojo.place(filterLink, filtersList);
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

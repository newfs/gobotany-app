// UI code for the Simple Key results/filter page.

dojo.provide('gobotany.sk.results');
dojo.require('dojox.data.JsonRestStore');
dojo.require('gobotany.filters');

gobotany.sk.results.show_filter_working = function(character_friendly_name,
                                                   character_short_name) {
    dojo.query('#filter-working').style({display: 'block'});
    dojo.query('#filter-working .name')[0].innerHTML = character_friendly_name;

    // TODO: Check the user's chosen item if this filter is "active."
    // (For now, just check Don't Know.)
    dojo.query('#filter-working .values input')[0].checked = true;
};

gobotany.sk.results.hide_filter_working = function() {
    dojo.query('#filter-working').style({display: 'none'});
};

gobotany.sk.results.populate_default_filters = function(pile_slug) {
    var filtersList = dojo.query('#filters ul')[0];
    dojo.empty(filtersList);

    var url = '/piles/';
    var store = new dojox.data.JsonRestStore({target: url});
    store.fetchItemByIdentity({
        identity: pile_slug,
        onItem: function(item) {
            for (var y = 0; y < item.default_filters.length; y++) {
                var filter = item.default_filters[y];
                dojo.place('<li><a href="javascript:gobotany.sk.results.' +
                           'show_filter_working(\'' +
                           filter.character_friendly_name + '\', \'' + 
                           filter.character_short_name + '\')">' +
                           filter.character_friendly_name +
                           '</a></li>', filtersList);
            }
        }
    });
};

gobotany.sk.results.init = function(pile_slug) {
    // Wire up the filter working area's close button.
    var el = dojo.query('#filter-working .close')[0];
    dojo.connect(el, 'onclick', null, 
                 gobotany.sk.results.hide_filter_working);

    // Create a FilterManager object, which will pull a list of default
    // filters for the pile.
    console.log('pile_slug: ' + pile_slug);
    var filter_manager = new FilterManager({ pile_slug: pile_slug });
    console.log(filter_manager.pile_slug);
    filter_manager.load_default_filters();
    console.log('filter_manager.default_filters: ' + filter_manager.default_filters);

    // Populate the initial list of default filters.
    gobotany.sk.results.populate_default_filters(pile_slug);
    // TODO: instead pass the FilterManager object, which holds the filters.
    // gobotany.sk.results.populate_default_filters(filter_manager);
};

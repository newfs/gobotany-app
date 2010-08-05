dojo.provide('gobotany.results');
dojo.require('dojox.data.JsonRestStore');

gobotany.results.show_filter_working = function(character_friendly_name, 
                                                character_short_name) {
    dojo.query('#filter-working').style({display: 'block'});
    dojo.query('#filter-working .name')[0].innerHTML = character_friendly_name;
};

gobotany.results.hide_filter_working = function() {
    dojo.query('#filter-working').style({display: 'none'});
};

gobotany.results.populate_default_filters = function(pile_slug) {
    var filtersList = dojo.query('#filters ul')[0];
    dojo.empty(filtersList);

    var url = '/piles/';
    var store = new dojox.data.JsonRestStore({target: url});
    store.fetchItemByIdentity({
        identity: pile_slug,
        onItem: function(item) {
            for (var y = 0; y < item.default_filters.length; y++) {
                var filter = item.default_filters[y];
                dojo.place('<li><a href="' +
                           'javascript:gobotany.results.show_filter_working(\'' + 
                           filter.character_friendly_name + '\', \'' + 
                           filter.character_short_name + '\')">' + 
                           filter.character_friendly_name +
                           '</a></li>', filtersList);
            }
        }
    });
};

gobotany.results.init = function(pile_slug) {
    // Wire up the filter working area's close button.
    var el = dojo.query('#filter-working .close')[0];
    dojo.connect(el, 'onclick', null, gobotany.results.hide_filter_working);

    // Populate the initial list of default filters.
    gobotany.results.populate_default_filters(pile_slug);
};

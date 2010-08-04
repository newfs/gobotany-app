dojo.provide('gobotany.results');
dojo.require('dojox.data.JsonRestStore');

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
                dojo.place('<li>' + filter.character_friendly_name +
                           '</li>', filtersList);
            }
        }
    });
};

gobotany.results.init = function(pile_slug) {
    gobotany.results.populate_default_filters(pile_slug);
};

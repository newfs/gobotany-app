dojo.provide('gobotany.results');
dojo.require('dojox.data.JsonRestStore');

gobotany.results.populate_default_filters = function(pile) {
    var filtersList = dojo.query('#filters ul')[0];
    dojo.empty(filtersList);

    var url = '/piles/'; // + pile; // ? for some reason fetch isn't returning
                                    // when pile added
    var store = new dojox.data.JsonRestStore({target: url});
    store.fetch({onComplete: function(response) {
        for (var x = 0; x < response.items.length; x++) {
            var item = response.items[x];
            if (item.name === pile) {
                for (var y = 0; y < item.default_filters.length; y++) {
                    var filter = item.default_filters[y];
                    dojo.place('<li>' + filter.character_friendly_name + 
                               '</li>', filtersList);
                }
            }
        }
    }});
};

gobotany.results.init = function(pile) {
    gobotany.results.populate_default_filters(pile);
};

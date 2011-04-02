// Global declaration for JSLint (http://www.jslint.com/)
/*global dojo, dojox */

dojo.provide('gobotany.piles');

dojo.declare('gobotany.piles.PileManager', null, {
    constructor: function(pile_slug) {
        this.pile_slug = pile_slug;
        this.pile_info = {};

        var piles_url = API_URL + 'piles/';
        this.store = new dojox.data.JsonRestStore({target: piles_url});
    },

    load: function() {
        this.store.fetchItemByIdentity({
            scope: this,
            identity: this.pile_slug,
            onItem: function(item) {
                this.pile_info = item;
                this.on_pile_info_changed(item);
            }
        });
    },

    on_pile_info_changed: function(pile_info) {}

});

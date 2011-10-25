// Global declaration for JSLint (http://www.jslint.com/)
/*global dojo, dojox */

dojo.provide('gobotany.piles');

dojo.declare('gobotany.piles.PileManager', null, {
    constructor: function(pile_slug) {
        this.pile_slug = pile_slug;
        this.pile_info = {};
    },

    load: function() {
        var t = this;
        simplekey_resources.pile(this.pile_slug).done(function(pile_info) {
            t.pile_info = pile_info;
            t.on_pile_info_changed(pile_info);
        });
    },

    on_pile_info_changed: function(pile_info) {}

});

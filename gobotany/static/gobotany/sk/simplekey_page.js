// Global declaration for JSLint (http://www.jslint.com/)
/*global dojo, dojox, dijit, gobotany */

dojo.provide('gobotany.sk.simplekey_page');

dojo.require('gobotany.filters');
dojo.require('gobotany.piles');
dojo.require('gobotany.sk.plant_preview');

dojo.require("dijit.Dialog");
dojo.require("dijit.form.Button");
dojo.require("dojo.NodeList-traverse");
dojo.require('dojox.embed.Flash');

gobotany.sk.simplekey_page.pile_slug = null;
gobotany.sk.simplekey_page.filter_manager = null;
gobotany.sk.simplekey_page.pile_manager = null;

gobotany.sk.simplekey_page.init = function() {

    /* A filter manager is needed by plant_preview.js. */
    gobotany.sk.simplekey_page.filter_manager =
        new gobotany.filters.FilterManager({
            pile_slug: 'none'
        });

    var image_buttons = dojo.query('.species_image_ribbon div');
    image_buttons.forEach(function(node) {
        dojo.connect(node, 'onclick', null, function(e) {
            dijit.byId('plant-preview').show();
            var img = dojo.query('img', node)[0];
            var plant = {
                scientific_name: img.getAttribute('scientific_name')
            };
            gobotany.sk.plant_preview.show_plant_preview(plant,
                gobotany.sk.simplekey_page.filter_manager.plant_preview_characters,
                img);
        });
    });

    dojo.query('.PileVideo').forEach(function(node, index, attr) {
        var path = dojo.attr(dojo.query('> a', node)[0], 'href');
        dojox.embed.Flash({path: path, width: 200, height: 200},
                          node);
    });

};

gobotany.sk.simplekey_page.toggle_tooltip = function(slug) {
    dojo.query('.PileInfo.tooltip').removeClass('active');
    var tooltip = dojo.byId(slug + '-tooltip');
    dojo.addClass(tooltip, 'active');

    gobotany.sk.simplekey_page.pile_slug = slug;
    gobotany.sk.simplekey_page.filter_manager.pile_slug = slug;

    // Initialize a pile manager
    gobotany.sk.simplekey_page.pile_manager =
        new gobotany.piles.PileManager({
            pile_slug: slug
        });
    gobotany.sk.simplekey_page.pile_manager.load();
};

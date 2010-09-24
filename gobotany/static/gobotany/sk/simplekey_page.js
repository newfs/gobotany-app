dojo.provide('gobotany.sk.simplekey_page');

dojo.require('gobotany.filters');
dojo.require('gobotany.sk.plant_preview');
dojo.require("dijit.Dialog");
dojo.require("dijit.TooltipDialog");
dojo.require("dijit.form.Button");
dojo.require("dijit.form.DropDownButton");
dojo.require("dojo.NodeList-traverse");
dojo.require('dojox.embed.Flash');

var filter_manager = null;

dojo.addOnLoad(function() {

    /* A filter manager is needed by plant_preview.js. */
    filter_manager = new gobotany.filters.FilterManager({
        pile_slug: 'none',
    });

    var image_buttons = dojo.query('.species_image_ribbon > .species_dropdown');
    image_buttons.forEach(function (node) {
        dojo.connect(node, "onclick", null, function (e) {
            /* The show_plant_preview() function needs the filter
               manager to know the current pile's slug in order to show
               the plant preview characters.  Is it cheating to grab the
               pile slug off of our enclosing PileInfo div? */
            var div = dojo.query(node).parents('.PileInfo')[0];
            var pile_slug = div.id.slice(0, -8);  /* remove '-tooltip' */
            filter_manager.pile_slug = pile_slug;
            filter_manager.load_pile_info();
            /* The show_plant_preview() function looks for the node with
               an id of 'plant-preview' to know where to do its work.
               Since clicking on an image might be bringing up any one
               of the several "dropdown" divs that Dijit has put down at
               the bottom of our body, we need to go find out which one
               has been selected and give it the 'plant-preview' id before
               starting up show_plant_preview().  Oh: and if someone else
               already has that id because of a previous click, we remove
               that id first.  Since ids are supposed to be unique and all. */
            var img = dojo.query('img', node)[0];
            var old = dojo.byId('plant-preview');
            if (old != null) {
                old.id = null;
            }
            var widget = dijit.byNode(this);
            var contentsnode = dojo.query('.dijitTooltipContents',
                                         widget.dropDown.domNode)[0];
            contentsnode.id = 'plant-preview';
            var plant = {
                scientific_name: img.getAttribute('scientific_name'),
            };
            gobotany.sk.plant_preview.show_plant_preview(plant,
                filter_manager.plant_preview_characters);
        });
    });
    dojo.query('.PileVideo').forEach(function (node, index, attr) {
        var path = dojo.attr(dojo.query('> a', node)[0], 'href');
        var player = new dojox.embed.Flash({path: path,
                                            width: 200,
                                            height: 200},
                                            node);
    });
});

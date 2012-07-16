// UI code for the Simple Key results/filter page.
define([
    'dojo/_base/declare',
    'dojo/_base/lang',
    'dojo/query',
    'dojo/NodeList-dom',
    'dojo/dom-attr',
    'dojo/dom-construct',
    'dojo/dom-style',
    'bridge/underscore',
    'gobotany/sk/SpeciesSectionHelper',
    'simplekey/resources',
    'simplekey/App3'
], function(declare, lang, query, nodeListDom, domAttr, domConstruct,
    domStyle, _, SpeciesSectionHelper,
    resources, App3) {

return declare('gobotany.sk.ResultsHelper', null, {

    constructor: function(pile_slug, plant_divs_ready) {
        // summary:
        //   Helper class for managing the sections on the results page.
        // description:
        //   Coordinates all of the dynamic logic on the results page.

        this.pile_slug = pile_slug;
        this.species_section =
            new SpeciesSectionHelper(pile_slug, plant_divs_ready);
    }
});

});

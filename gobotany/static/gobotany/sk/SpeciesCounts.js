/*
 * Manage everywhere on the page that we maintain a species count.
 */
define([
    'dojo/_base/declare',
    'dojo/_base/fx',
    'dojo/NodeList-fx',
    'dojo/query',
    'simplekey/App3'
], function(declare, fx, nodeListFx, query, App3) {

return declare('gobotany.sk.SpeciesCounts', null, {
    animation: null,

    _update_counts: function(species_list) {
        App3.taxa.set('len', species_list.length);

        if (this.animation !== null)
            this.animation.stop();

        var span = query('.species-count-heading > span');
        this.animation = span.animateProperty({
            duration: 2000,
            properties: {
                backgroundColor: {
                    start: '#FF0',
                    end: '#F0F0C0'
                }
            }
        });
        this.animation.play();
    }
});
});


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
    },

    load_selected_image_type: function(event) {
        var image_type = App3.get('image_type');
        if (!image_type)
            // No image types available yet, so skip for now
            return;

        /* Replace the image for each plant on the page */

        $('div.plant img').each(function(i, img) {

            // See if the taxon has an image for the new image type.
            var $img = $(img);
            var scientific_name = $img.attr('x-plant-id');
            var taxon = App3.taxa_by_sciname[scientific_name];
            var new_image = _.find(taxon.images, function(image) {
                return image.type === image_type});

            if (new_image) {
                $img.attr('x-tmp-src', new_image.thumb_url);
                $img.attr('alt', new_image.title);
                // Hide the empty box if it exists and make
                // sure the image is visible.
                $img.find('+ div.missing-image').remove();
                $img.css('display', 'inline');

            } else if ($img.css('display') !== 'none') {
                // If there's no matching image display the
                // empty box and hide the image
                $img.css('display', 'none');
                $('<div>', {
                    'class': 'missing-image',
                    'innerHTML': '<p>Image not available yet</p>'
                }).appendTo($img);
            }
        });
        this.species_section.lazy_load_images();
    }
});

});

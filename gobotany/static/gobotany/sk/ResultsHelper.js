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

        resources.pile(this.pile_slug).done(
            lang.hitch(this, function(pile_info) {
                this._setup_character_groups(pile_info.character_groups);
            }));
    },

    _setup_character_groups: function(character_groups) {
        var $ul = $('ul.char-groups').empty();
        _.each(character_groups, function(character_group) {
            $ul.append(
                $('<li>').append(
                    $('<label>').append(
                        $('<input>', {type: 'checkbox',
                                      value: character_group.id}),
                        ' ' + character_group.name
                    )
                )
            );
        });
    },

    load_selected_image_type: function(event) {
        var image_type = App3.get('image_type');
        if (!image_type) {
            // No image types available yet, so skip for now
            return;
        }

        var image_tags = query('div.plant img');
        // Replace the image for each plant on the page
        var i;
        for (i = 0; i < image_tags.length; i++) {
            var image_tag = image_tags[i];

            // See if the taxon has an image for the new image type.
            var scientific_name = domAttr.get(image_tag, 'x-plant-id');
            taxon = App3.taxa_by_sciname[scientific_name];
            var new_image = _.find(taxon.images, function(image) {
                return image.type === image_type});

            if (new_image) {
                domAttr.set(image_tag, 'x-tmp-src', new_image.thumb_url);
                domAttr.set(image_tag, 'alt', new_image.title);
                // Hide the empty box if it exists and make
                // sure the image is visible.
                query('+ div.missing-image', image_tag).orphan();
                domStyle.set(image_tag, 'display', 'inline');

            } else if (domStyle.get(image_tag, 'display') !== 'none') {
                // If there's no matching image display the
                // empty box and hide the image
                domStyle.set(image_tag, 'display', 'none');
                domConstruct.create('div', {
                    'class': 'missing-image',
                    'innerHTML': '<p>Image not available yet</p>'
                }, image_tag, 'after');
            }
        }
        this.species_section.lazy_load_images();
    }
});

});

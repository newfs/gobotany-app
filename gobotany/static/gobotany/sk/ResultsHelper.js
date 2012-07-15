// UI code for the Simple Key results/filter page.
define([
    'dojo/_base/declare',
    'dojo/_base/lang',
    'dojo/on',
    'dojo/keys',
    'dojo/query',
    'dojo/NodeList-dom',
    'dojo/dom-attr',
    'dojo/dom-construct',
    'dojo/dom-style',
    'bridge/underscore',
    'gobotany/sk/FilterSectionHelper',
    'gobotany/sk/SpeciesSectionHelper',
    'simplekey/resources',
    'simplekey/App3'
], function(declare, lang, on, keys, query, nodeListDom, domAttr, domConstruct,
    domStyle, _, FilterSectionHelper, SpeciesSectionHelper,
    resources, App3) {

return declare('gobotany.sk.ResultsHelper', null, {

    constructor: function(pile_slug, plant_divs_ready) {
        // summary:
        //   Helper class for managing the sections on the results page.
        // description:
        //   Coordinates all of the dynamic logic on the results page.

        this.pile_slug = pile_slug;
        this.animation = null;
        this.species_section =
            new SpeciesSectionHelper(pile_slug, plant_divs_ready);
        this.filter_section = new FilterSectionHelper(this);

        resources.pile(this.pile_slug).done(
            lang.hitch(this, function(pile_info) {
                this.filter_section._setup_character_groups(
                    pile_info.character_groups);
            }));

        // Set up a handler to detect an Esc keypress, which will close
        // the filter working area if it is open.
        on(document.body, 'keypress',
            lang.hitch(this, this.handle_keys));
    },

    handle_keys: function(e) {
        switch (e.charOrCode) {
            case keys.ESCAPE:
                if (this.filter_section.working_area) {
                    this.filter_section.working_area.dismiss();
                }
                break;
        }
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
    },

    update_counts: function(species_list) {
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

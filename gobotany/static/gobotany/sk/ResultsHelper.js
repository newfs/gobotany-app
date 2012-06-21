// UI code for the Simple Key results/filter page.
define([
    'gobotany/sk/FilterSectionHelper',
    'gobotany/sk/SpeciesSectionHelper',
    'gobotany/sk/working_area'
], function() {

dojo.declare('gobotany.sk.ResultsHelper', null, {

    constructor: function(pile_slug, plant_divs_ready) {
        // summary:
        //   Helper class for managing the sections on the results page.
        // description:
        //   Coordinates all of the dynamic logic on the results page.

        this.pile_slug = pile_slug;

        this.species_section =
            new gobotany.sk.SpeciesSectionHelper(pile_slug, plant_divs_ready);

        this.species_counts =
        new gobotany.sk.SpeciesCounts(this);

        this.filter_section =
            new gobotany.sk.FilterSectionHelper(this);

        simplekey_resources.pile(this.pile_slug).done(
            dojo.hitch(this, function(pile_info) {
                this.filter_section._setup_character_groups(
                    pile_info.character_groups);
            }));

        // Set up a handler to detect an Esc keypress, which will close
        // the filter working area if it is open.
        dojo.connect(document.body, 'onkeypress',
            dojo.hitch(this, this.handle_keys));
    },

    handle_keys: function(e) {
        switch (e.charOrCode) {
            case dojo.keys.ESCAPE:
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

        var image_tags = dojo.query('div.plant img');
        // Replace the image for each plant on the page
        var i;
        for (i = 0; i < image_tags.length; i++) {
            var image_tag = image_tags[i];

            // See if the taxon has an image for the new image type.
            var scientific_name = dojo.attr(image_tag, 'x-plant-id');
            taxon = App3.taxa_by_sciname[scientific_name];
            var new_image = _.find(taxon.images, function(image) {
                return image.type === image_type});

            if (new_image) {
                dojo.attr(image_tag, 'x-tmp-src', new_image.thumb_url);
                dojo.attr(image_tag, 'alt', new_image.title);
                // Hide the empty box if it exists and make
                // sure the image is visible.
                dojo.query('+ div.missing-image', image_tag).orphan();
                dojo.style(image_tag, 'display', 'inline');

            } else if (dojo.style(image_tag, 'display') !== 'none') {
                // If there's no matching image display the
                // empty box and hide the image
                dojo.style(image_tag, 'display', 'none');
                dojo.create('div', {
                    'class': 'missing-image',
                    'innerHTML': '<p>Image not available yet</p>'
                }, image_tag, 'after');
            }
        }
        this.species_section.lazy_load_images();
    }
});

return gobotany.sk.ResultsHelper;
});

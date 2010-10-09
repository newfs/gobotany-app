dojo.provide('gobotany.sk.plant_preview');

dojo.require('dojox.data.JsonRestStore');
dojo.require('gobotany.sk.image_browse');

// Image info storage for images that appear on the plant preview dialog box.
gobotany.sk.plant_preview.images = [];

gobotany.sk.plant_preview.change_image = function(event) {
    event.preventDefault();

    var img = dojo.query('#plant-preview .photos img')[0];
    var current_image_url = dojo.attr(img, 'src');

    // Figure out the index of the image that is showing.
    var current_image_index =
        gobotany.sk.image_browse.get_current_image_index(current_image_url,
            gobotany.sk.plant_preview.images, 'scaled_url');

    // Figure out which image to show next.
    var new_image_index = gobotany.sk.image_browse.get_next_image_index(
        '#plant-preview .photos', gobotany.sk.plant_preview.images.length,
        current_image_index);

    // Change the image and update the position/count message.
    var msg = dojo.query('#plant-preview .photos span')[0];
    var image = gobotany.sk.plant_preview.images[new_image_index];
    gobotany.sk.image_browse.set_image(img, msg, image.scaled_url,
        image.title, new_image_index, 
        gobotany.sk.plant_preview.images.length);
};

gobotany.sk.plant_preview.show_plant_preview = function(plant,
                                               plant_preview_characters,
                                               clicked_image) {
    dojo.query('#plant-preview h3')[0].innerHTML = '<i>' +
        plant.scientific_name + '</i>';
    var list = dojo.query('#plant-preview dl')[0];
    dojo.empty(list);

    // Clear the images area.
    var img = dojo.query('#plant-preview .photos img')[0];
    dojo.attr(img, 'src', '');
    dojo.attr(img, 'alt', 'image not available');
    var msg = dojo.query('#plant-preview .photos span')[0];
    msg.innerHTML = '';

    taxon_button = dojo.query('#plant-preview .nav button')[0];
    dojo.connect(dijit.byId('taxon_button'), 'onClick', function() {
        url = window.location.href.split('#')[0] +
              plant.scientific_name.toLowerCase().replace(' ', '/') + '/';
        window.location.href = url;
    });

    taxon_url = '/taxon/' + plant.scientific_name + '/';
    var taxon_store = new dojox.data.JsonRestStore({target: taxon_url});
    taxon_store.fetch({
        onComplete: function(taxon) {
            // List any designated characters and their values.
            for (var i = 0; i < plant_preview_characters.length; i++) {
                var ppc = plant_preview_characters[i];
                dojo.create('dt', {innerHTML: ppc.character_friendly_name},
                            list);
                dojo.create('dd',
                            {innerHTML: taxon[ppc.character_short_name]},
                            list);
                }

            // List the collections (piles) to which this plant belongs.
            dojo.create('dt', {innerHTML: 'Collection'}, list);
            var piles = '';
            for (var i = 0; i < taxon.piles.length; i++) {
                if (i > 0) {
                    piles += ', ';
                }
                piles += taxon.piles[i];
            }
            dojo.create('dd', {innerHTML: piles}, list);

            gobotany.sk.plant_preview.images = [];
            if (taxon.images.length) {
                // Store the info for the images to allow for browsing them.
                for (var i = 0; i < taxon.images.length; i++) {
                    gobotany.sk.plant_preview.images.push(taxon.images[i]);
                }
                // If the alt text of the thumbnail the user clicked on in the
                // page is different from the alt text of the first image
                // showing on the popup, look for matching alt text and show
                // that image first on the popup.
                var clicked_image_alt_text = dojo.attr(clicked_image, 'alt');
                var first_image_index = 0;
                for (var i = 0; i < gobotany.sk.plant_preview.images.length;
                    i++) {

                    if (clicked_image_alt_text ===
                        gobotany.sk.plant_preview.images[i].title) {

                        first_image_index = i;
                        break;
                    }
                }
                var image = 
                    gobotany.sk.plant_preview.images[first_image_index];
                gobotany.sk.image_browse.set_image(img, msg, image.scaled_url,
                    image.title, first_image_index, taxon.images.length);
            }

            // Wire up the previous and next links, or hide them if
            // they're not needed.
            gobotany.sk.image_browse.set_up_navigation_links(taxon.images,
                '#plant-preview .photos', gobotany.sk.plant_preview.change_image);
        }
    });
};

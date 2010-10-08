dojo.provide('gobotany.sk.plant_preview');

dojo.require('dojox.data.JsonRestStore');

// Image info storage for images that appear on the plant preview dialog box.
gobotany.sk.plant_preview.plant_preview_images = [];

gobotany.sk.plant_preview.change_plant_preview_image = function(event) {
    event.preventDefault();
    //alert('this.innerHTML: ' + this.innerHTML);
    var img = dojo.query('#plant-preview .photos img')[0];
    var current_image_url = dojo.attr(img, 'src');

    var current_image_index = null;
    var i = 0;
    while (current_image_index === null &&
           i < gobotany.sk.plant_preview.plant_preview_images.length) {
        if (current_image_url ===
            gobotany.sk.plant_preview.plant_preview_images[i].scaled_url) {

            current_image_index = i;
        }
        i++;
    }

    // Figure out which image to show next.
    var new_image_index = current_image_index;
    if (this.innerHTML.indexOf('next') >= 0) {
        new_image_index++;
    }
    else if (this.innerHTML.indexOf('prev') >= 0) {
        new_image_index--;
    }
    if (new_image_index < 0) {
        new_image_index =
            gobotany.sk.plant_preview.plant_preview_images.length - 1;
    }
    else if (new_image_index >
             gobotany.sk.plant_preview.plant_preview_images.length - 1) {
        new_image_index = 0;
    }

    // Change the image.
    dojo.attr(img, 'src', gobotany.sk.plant_preview.plant_preview_images[
                          new_image_index].scaled_url);
    dojo.attr(img, 'alt', gobotany.sk.plant_preview.plant_preview_images[
                          new_image_index].title);
    // Update the position/count message.
    var msg = dojo.query('#plant-preview .photos span')[0];
    msg.innerHTML = (new_image_index + 1) + ' of ' +
        gobotany.sk.plant_preview.plant_preview_images.length;
};

gobotany.sk.plant_preview.set_image = function(image_node, message_node,
                                      plant_image, index, num_images) {
    dojo.attr(image_node, 'src', plant_image.scaled_url);
    // TODO: is this title field intended/sufficient for alt text?
    dojo.attr(image_node, 'alt', plant_image.title);
    // Set the count message.
    message_node.innerHTML = (index + 1) + ' of ' + num_images;
};

gobotany.sk.plant_preview.show_plant_preview = function(plant,
                                               plant_preview_characters,
                                               clicked_image_alt_text) {
    dojo.query('#plant-preview h3')[0].innerHTML = '<i>' +
        plant.scientific_name + '</i>';
    var list = dojo.query('#plant-preview dl')[0];
    dojo.empty(list);

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

            // Clear the images area.
            var img = dojo.query('#plant-preview .photos img')[0];
            dojo.attr(img, 'src', '');
            dojo.attr(img, 'alt', 'image not available');
            var msg = dojo.query('#plant-preview .photos span')[0];
            msg.innerHTML = '';

            gobotany.sk.plant_preview.plant_preview_images = [];
            if (taxon.images.length) {
                // Store the info for the images to allow for browsing them.
                for (var i = 0; i < taxon.images.length; i++) {
                    gobotany.sk.plant_preview.plant_preview_images.push(
                        taxon.images[i]);
                }
                // If the alt text of the thumbnail the user clicked on in the
                // initial view of the page is different from the alt text of
                // the first image showing on the popup, look for matching alt
                // text and show that image first on the popup. These will
                // only match the initial image type (e.g., habit) so far,
                // because the other views' alt text doesn't come through.
                // TODO: verify that we are changing the alt text when we are
                // changing the images to a new type.
                var first_image_index = 0;
                for (var i = 0;
                    i < gobotany.sk.plant_preview.plant_preview_images.length;
                    i++) {

                    if (clicked_image_alt_text ===
                        gobotany.sk.plant_preview.plant_preview_images[i].title) {

                        first_image_index = i;
                        break;
                    }
                }
                gobotany.sk.plant_preview.set_image(img, msg,
                    gobotany.sk.plant_preview.plant_preview_images[first_image_index],
                    first_image_index, taxon.images.length);
            }

            // Wire up the previous and next links, or hide them if
            // they're not needed.
            var links = dojo.query('#plant-preview .photos a');
            for (var i = 0; i < links.length; i++) {
                if (taxon.images.length > 1) {
                    dojo.removeClass(links[i], 'hidden');
                    dojo.connect(links[i], 'onclick',
                        gobotany.sk.plant_preview.change_plant_preview_image);
                }
                else {
                    dojo.addClass(links[i], 'hidden');
                }
            }
        }
    });
};

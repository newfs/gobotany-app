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

gobotany.sk.plant_preview.show_plant_preview = function(plant) {
    dojo.query('#plant-preview h3')[0].innerHTML = '<i>' +
        plant.scientific_name + '</i>';
    var list = dojo.query('#plant-preview dl')[0];
    dojo.empty(list);

    var taxon_store = new dojox.data.JsonRestStore(
        {target: '/taxon/' + plant.scientific_name});
    taxon_store.fetch({
        onComplete: function(taxon) {
            for (var i = 0;
                 i < filter_manager.plant_preview_characters.length; i++) {
                var ppc = filter_manager.plant_preview_characters[i];
                dojo.create('dt', {innerHTML: ppc.character_friendly_name},
                            list);
                dojo.create('dd',
                            {innerHTML: taxon[ppc.character_short_name]},
                            list);
            }
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
                // Set the first image.
                dojo.attr(img, 'src',
                    gobotany.sk.plant_preview.plant_preview_images[0].scaled_url);
                // TODO: is this title field intended/sufficient for alt text?
                dojo.attr(img, 'alt',
                    gobotany.sk.plant_preview.plant_preview_images[0].title);
                // Set the count message.
                msg.innerHTML = '1 of ' + taxon.images.length;
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

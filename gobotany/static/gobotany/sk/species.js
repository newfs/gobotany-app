dojo.provide('gobotany.sk.species');

dojo.require('dojox.data.JsonRestStore');

dojo.require('gobotany.sk.glossarize');
dojo.require('gobotany.sk.image_browse');

// Image info storage for images that appear on the species page.
gobotany.sk.species.images = [];

gobotany.sk.species.change_image = function(event) {
    event.preventDefault();

    var img = dojo.query('#species #images img')[0];
    var current_image_url = dojo.attr(img, 'src');

    // Figure out the index of the image that is showing.
    var current_image_index =
        gobotany.sk.image_browse.get_current_image_index(current_image_url,
            gobotany.sk.species.images, 'url');

    // Figure out which image to show next.
    var new_image_index = gobotany.sk.image_browse.get_next_image_index(
        '#species #images', gobotany.sk.species.images.length,
        current_image_index);

    // Change the image and update the position/count message.
    var msg = dojo.query('#species #images span')[0];
    var image = gobotany.sk.species.images[new_image_index];
    gobotany.sk.image_browse.set_image(img, msg, image.url,
        image.title, new_image_index, gobotany.sk.species.images.length);
};

gobotany.sk.species.init = function(scientific_name) {
    var img = dojo.query('#species #images img')[0];
    var msg = dojo.query('#species #images span')[0];
    
    // Load the taxon URL and set up the images.
    taxon_url = '/taxon/' + scientific_name + '/';
    var taxon_store = new dojox.data.JsonRestStore({target: taxon_url});
    taxon_store.fetch({
        onComplete: function(taxon) {
            gobotany.sk.species.images = [];
            if (taxon.images.length) {
                // Store the info for the images to allow for browsing them.
                for (var i = 0; i < taxon.images.length; i++) {
                    gobotany.sk.species.images.push(taxon.images[i]);
                }
                // If the alt text of the thumbnail the user clicked on in the
                // page is different from the alt text of the first image
                // showing on the popup, look for matching alt text and show
                // that image first on the popup.
                
                // TODO: pass image that was visible on the plant preview
                // popup when the user came to the species page.
                //var clicked_image_alt_text = dojo.attr(clicked_image, 'alt');
                var preview_image_alt_text = 'TODO';
                
                var first_image_index = 0;
                for (i = 0; i < gobotany.sk.species.images.length; i++) {

                    if (preview_image_alt_text ===
                        gobotany.sk.species.images[i].title) {

                        first_image_index = i;
                        break;
                    }
                }
                var image = gobotany.sk.species.images[first_image_index];
                gobotany.sk.image_browse.set_image(img, msg, image.url,
                    image.title, first_image_index, taxon.images.length);
            }

            // Wire up the previous and next links, or hide them if
            // they're not needed.
            gobotany.sk.image_browse.set_up_navigation_links(taxon.images,
                '#species #images', gobotany.sk.species.change_image);
        }
    });
    
    // Make glossary highlights appear where appropriate throughout the page.
    var glossarizer = gobotany.sk.results.Glossarizer();
    dojo.query('#info p').forEach(function(node) {
        glossarizer.markup(node);
    });
};

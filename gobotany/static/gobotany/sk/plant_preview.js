dojo.provide('gobotany.sk.plant_preview');

dojo.require('dojox.data.JsonRestStore');
dojo.require('gobotany.sk.images.ImageBrowser');

gobotany.sk.plant_preview.show_plant_preview = function(plant,
                                               plant_preview_characters,
                                               clicked_image) {
    dojo.query('#plant-preview h3')[0].innerHTML = '<i>' +
        plant.scientific_name + '</i>';
    var list = dojo.query('#plant-preview dl')[0];
    dojo.empty(list);

    var image_browser = gobotany.sk.images.ImageBrowser();
    image_browser.css_selector = '#plant-preview .photos';
    image_browser.url_key = 'scaled_url';

    dojo.connect(dijit.byId('taxon_button'), 'onClick', function() {
        var path = window.location.pathname.split('#')[0];
        var re = /^\/simple\/.[^\/]*\/$/;
        if (path.match(re)) {
            // If on a 'numbered' collection page or other pile group page,
            // use the generic path to a species page rather than the usual
            // full pile path.
            path = '/simple/species/';
        }
        var url = path + plant.scientific_name.toLowerCase().replace(
            ' ', '/') + '/';
        window.location.href = url;
    });

    var taxon_url = '/taxon/' + plant.scientific_name + '/';
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
            for (i = 0; i < taxon.piles.length; i++) {
                if (i > 0) {
                    piles += ', ';
                }
                piles += taxon.piles[i];
            }
            dojo.create('dd', {innerHTML: piles}, list);

            gobotany.sk.plant_preview.images = [];
            if (taxon.images.length) {
                // Store the info for the images to allow for browsing them.
                for (i = 0; i < taxon.images.length; i++) {
                    image_browser.images.push(taxon.images[i]);
                }
                // If the alt text of the thumbnail the user clicked on in the
                // page is different from the alt text of the first image
                // showing on the popup, look for matching alt text and show
                // that image first on the popup.
                if ((clicked_image !== undefined) && (clicked_image.length)) {
                    var clicked_image_alt_text = dojo.attr(clicked_image,
                        'alt');
                    for (i = 0; i < image_browser.images.length; i++) {
                        if (clicked_image_alt_text ===
                            image_browser.images[i].title) {

                            image_browser.first_image_index = i;
                            break;
                        }
                    }
                }
            }

            image_browser.setup();
        }
    });
};

// Global declaration for JSLint (http://www.jslint.com/)
/*global dojo, dojox, dijit, gobotany, window */

dojo.provide('gobotany.sk.plant_preview');

dojo.require('gobotany.sk.images.ImageBrowser');
dojo.require('gobotany.sk.partners');
dojo.require('gobotany.utils');

dojo.require('dojox.data.JsonRestStore');

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
            var partner_site = gobotany.sk.partners.partner_site();
            console.log('partner_site: ' + partner_site);
            // List any designated characters and their values.
            for (var i = 0; i < plant_preview_characters.length; i++) {
                var ppc = plant_preview_characters[i];
                if (ppc.partner_site === partner_site) {
                    dojo.create('dt',
                        {innerHTML: ppc.character_friendly_name},
                        list);
                    var display_value = '';
                    var character_value = taxon[ppc.character_short_name];
                    if (character_value !== undefined) {
                        display_value = character_value;
                        if (ppc.value_type === 'LENGTH') {
                            var min = character_value[0];
                            var max = character_value[1];
                            display_value = gobotany.utils.pretty_length(
                                ppc.unit, min) + ' to ' +
                                gobotany.utils.pretty_length(ppc.unit, max);
                        }
                    }
                    dojo.create('dd', {innerHTML: display_value}, list);
                }
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

            image_browser.images = [];
            if (taxon.images.length) {
                // Store the info for the images to allow for browsing them.
                for (i = 0; i < taxon.images.length; i++) {
                    image_browser.images.push(taxon.images[i]);
                }
                // Compare the alt text of the thumbnail the user clicked on
                // with that of each image. Show the image that has alt text
                // that matches the thumbnail alt text.
                if (clicked_image !== undefined) {
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

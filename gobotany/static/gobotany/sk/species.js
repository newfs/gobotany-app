dojo.provide('gobotany.sk.species');

dojo.require('dijit.TitlePane');
dojo.require('dojo.cookie');
dojo.require('dojox.data.JsonRestStore');

dojo.require('gobotany.sk.glossarize');
dojo.require('gobotany.sk.images.ImageBrowser');

// Image info storage for images that appear on the species page.
gobotany.sk.species.images = [];

gobotany.sk.species.close_character_sections = function() {
    // Close all the expandable sections for the character groups.
    dojo.query('#species div.dijitTitlePane').forEach(function(div) {
        var div_id = dojo.attr(div, 'id');
        var widget = dijit.byId(div_id);
        if (widget.open) {
            widget.toggle();
        }
    });
}

gobotany.sk.species.init = function(scientific_name) {
    gobotany.sk.species.close_character_sections();

    // Set up the image browser and load the image information.

    var image_browser = gobotany.sk.images.ImageBrowser();
    image_browser.css_selector = '#species #images';

    taxon_url = '/taxon/' + scientific_name + '/';
    var taxon_store = new dojox.data.JsonRestStore({target: taxon_url});
    taxon_store.fetch({
        onComplete: function(taxon) {
            if (taxon.images.length) {
                for (var i = 0; i < taxon.images.length; i++) {
                    image_browser.images.push(taxon.images[i]);
                }
                // If the alt text of the thumbnail the user clicked on in the
                // page is different from the alt text of the first image
                // showing on the popup, look for matching alt text and show
                // that image first on the popup.
                //
                // TODO: pass image that was visible on the plant preview
                // popup when the user came to the species page.
                // Like in plant_preview.js, e.g.:
                //var clicked_image_alt_text = dojo.attr(clicked_image, 'alt');
                //
                //var preview_image_alt_text = 'TODO';
                //
                //for (var i = 0; i < image_browser.images.length; i++) {
                //    if (preview_image_alt_text ===
                //        image_browser.images[i].title) {
                //
                //        image_browser.first_image_index = i;
                //        break;
                //    }
                //}
            }

            image_browser.setup();
        }
    });


    // Make glossary highlights appear where appropriate throughout the page.
    var glossarizer = gobotany.sk.results.Glossarizer();
    dojo.query('#info p').forEach(function(node) {
        glossarizer.markup(node);
    });

    // Check for whether the stored filter-state cookie pertains to the
    // pile/results page for this plant. If so, replace the hyperlink href
    // for the pile/results page with the URL from the cookie in order to
    // persist filter state when the user clicks the link to go back.
    var last_plant_id_url = dojo.cookie('last_plant_id_url');
    var url_parts = window.location.toString().split('/');
    var pile_results_url = url_parts.slice(0, 6).join('/');
    if (last_plant_id_url.indexOf(pile_results_url) !== -1) {
        var link = dojo.byId('results-link');
        dojo.attr(link, 'href', last_plant_id_url);
    }
};

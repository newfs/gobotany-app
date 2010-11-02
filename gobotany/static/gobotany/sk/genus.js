dojo.provide('gobotany.sk.genus');

dojo.require('dojox.data.JsonRestStore');

dojo.require('gobotany.sk.glossarize');
dojo.require('gobotany.sk.images.ImageBrowser');

gobotany.sk.genus.init = function(genus_slug) {
    var image_browser = gobotany.sk.images.ImageBrowser();
    image_browser.css_selector = '#genus #images';

    // Load the genus URL and set up the images.
    var genus_url = '/genera/' + genus_slug + '/';
    var genus_store = new dojox.data.JsonRestStore({target: genus_url});
    // TODO: call genus URL as is done with taxon URL for species pages


    // Make glossary highlights appear where appropriate throughout the page.
    var glossarizer = gobotany.sk.results.Glossarizer();
    dojo.query('#info p').forEach(function(node) {
        glossarizer.markup(node);
    });
}

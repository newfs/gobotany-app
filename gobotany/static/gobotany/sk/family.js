dojo.provide('gobotany.sk.family');

dojo.require('dojox.data.JsonRestStore');

dojo.require('gobotany.sk.glossarize');
dojo.require('gobotany.sk.images.ImageBrowser');

gobotany.sk.family.init = function(family_slug) {
    var image_browser = gobotany.sk.images.ImageBrowser();
    image_browser.css_selector = '#family #images';
    
    // Load the family URL and set up the images.
    var family_url = '/families/' + family_slug + '/';
    var family_store = new dojox.data.JsonRestStore({target: family_url});
    // TODO: call family URL as is done with taxon URL for species pages


    // Make glossary highlights appear where appropriate throughout the page.
    var glossarizer = gobotany.sk.results.Glossarizer();
    dojo.query('#info p').forEach(function(node) {
        glossarizer.markup(node);
    });
}

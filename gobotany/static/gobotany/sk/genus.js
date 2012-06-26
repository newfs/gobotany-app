// Global declaration for JSLint (http://www.jslint.com/)
/*global dojo, dojox, gobotany */
define([
    'dojo/query',
    'bridge/jquery',
    'bridge/shadowbox',
    'gobotany/sk/photo'
], function(query, $, Shadowbox, PhotoHelper) {

var genus = {};
genus.init = function(genus_slug) {
    var photo_helper = PhotoHelper();
    
    // Wire up each image link to a Shadowbox popup handler.
    var IMAGE_CSS = '.pics .plant';
    query(IMAGE_CSS).forEach(function(plant_image_div) {
        var frame = $(plant_image_div).children('.frame');
        var link = $(plant_image_div).children('a');
        var href = $(link).attr('href');
        var title = $(link).attr('title');
        $(frame).click(function() {
            // Open the image.
            Shadowbox.open({
                content: href,
                player: 'img',
                title: title,
                options: {
                    onOpen: photo_helper.prepare_to_enlarge,
                    onFinish: photo_helper.process_credit
                }
            });
        });
    });
};
});

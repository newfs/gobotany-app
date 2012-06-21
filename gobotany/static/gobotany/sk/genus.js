// Global declaration for JSLint (http://www.jslint.com/)
/*global dojo, dojox, gobotany */

dojo.provide('gobotany.sk.genus');

dojo.require('gobotany.sk.photo');

gobotany.sk.genus.init = function(genus_slug) {
    var photo_helper = gobotany.sk.photo.PhotoHelper();
    
    // Wire up each image link to a Shadowbox popup handler.
    var IMAGE_CSS = '.pics .plant';
    dojo.query(IMAGE_CSS).forEach(function(plant_image_div) {
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

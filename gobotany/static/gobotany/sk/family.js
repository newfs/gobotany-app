define([
    'bridge/jquery',
    'bridge/shadowbox',
    'gobotany/sk/PhotoHelper'
], function($, Shadowbox, PhotoHelper) {
var family = {};
family.init = function(family_slug) {
    var photo_helper = PhotoHelper();
    
    // Wire up each image link to a Shadowbox popup handler.
    var IMAGE_CSS = '.pics .plant';
    $(IMAGE_CSS).each(function(i, plant_image_div) {
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
}

return family;
});

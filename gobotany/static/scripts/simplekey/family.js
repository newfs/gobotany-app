define([
    'bridge/jquery',
    'gobotany/sk/PhotoHelper',
    'util/sidebar',
    'util/activate_search_suggest',
    'util/shadowbox_init',
    'simplekey/glossarize'
], function($, PhotoHelper, sidebar, activate_search_suggest,
            shadowbox_init, glossarize) {

    var family = {};

    var _setup_page = function(args) {
        glossarize($('.description'));
        sidebar.setup();

        var photo_helper = PhotoHelper();

        // Wire up each image link to a Shadowbox popup handler.
        var $images = $('.pics .plant');
        $images.each(function(i, plant_image_div) {
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

    family.init = function(args) {
        $(document).ready(function() {
            _setup_page(args);
        });
    };

    return family;
});

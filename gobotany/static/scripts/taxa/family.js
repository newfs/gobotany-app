define([
    'bridge/jquery',
    'simplekey/PhotoHelper',
    'util/glossarizer',
    'util/shadowbox_init',
    'util/sidebar'
], function($, PhotoHelper, glossarizer, shadowbox_init, sidebar) {

    var exports = {};

    var _setup_page = function(args) {
        glossarizer.glossarize($('.description'));
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

    exports.init = function(args) {
        $(document).ready(function() {
            _setup_page(args);
        });
    };

    return exports;
});

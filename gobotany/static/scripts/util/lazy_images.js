/* Support lazy loading of images when they are scrolled into view. */

define([
    'bridge/jquery',
    'bridge/underscore'
], function($, _) {

    var module = {};

    /* How long to wait in milliseconds for various events to settle out
       and stop occurring before we bother running our check for newly-
       visible images. */

    module.SCROLL_WAIT = 0;  // for when they hold the up or down arrow
    module.RESIZE_WAIT = 500;

    module.start = function() {
        var timer;
        var reset = function(wait) {
            window.clearTimeout(timer);
            timer = setTimeout(module.load, wait);
        };
        $(window).scroll(function() {reset(module.SCROLL_WAIT)});
        $(window).resize(function() {reset(module.RESIZE_WAIT)});
    };

    module.load = function() {
        var view_top = $(window).scrollTop();
        var view_bottom = view_top + $(window).height();

        $('img[data-lazy-img-src]:visible').each(function(i, img) {
            var $img = $(img);

            var img_top = $img.offset().top;
            if (img_top > view_bottom) return;

            var img_bottom = img_top + $img.height();
            if (img_bottom < view_top) return;

            // Therefore, the image is visible!

            $img.attr('src', $img.attr('data-lazy-img-src'));
            $img.removeAttr('data-lazy-img-src');
        });
    };

    return module;
});

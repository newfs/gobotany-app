/*
 * Activate any class="img-container" elements to make them scrollable
 * using their "prev" and "next" buttons.
 */

require([
    'jquery.tools.min',
    'jquery.mousewheel.min'
], function() {

    $(document).ready(function() {

        // Turn on the scrollable for every gallery.

        $('.img-container').scrollable({keyboard: false});

        // For each gallery, clicking its frame should bring up Shadowbox.

        $('.img-gallery').each(function() {
            var gallery = this;
            $(gallery).children('.frame').click(function() {
                var container = $(gallery).children('.img-container');
                var scroll = container.data('scrollable');
                var a = scroll.getItems()[scroll.getIndex()];
                var rel = $(a).attr('rel');
                var galleryname = rel.split('[')[1].split(']')[0];
                Shadowbox.open({
                    content: a,
                    gallery: galleryname,
                    player: 'img',
                    options: {counterType: 'skip', overlayOpacity: 0.8}
                });
            });
        });

    });
});

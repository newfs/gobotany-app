/*
 * Activate any class="img-container" elements to make them scrollable
 * using their "prev" and "next" buttons.
 * 
 * For species pages, where the images are nested deeper in the HTML
 * for the scrolling presentation, use a different class: scrollWrapper.
 */

define([
    'bridge/jquery',
    'bridge/jquery.mousewheel',
    'bridge/shadowbox',
    'util/PhotoHelper'
], function ($, mousewheel, Shadowbox, PhotoHelper) {

    function ImageGallery() {
        // constructor
    }
    
    ImageGallery.prototype.activate = function () {
        // Turn on the scrollable control for every gallery.

        var scrollItemsSelector = '.img-container';
        if ($('body#species').length > 0) {
            // species page: scrolling container
            scrollItemsSelector = '.scrollWrapper';
        }
        $(scrollItemsSelector).scrollable({keyboard: false});

        // For each gallery, clicking its frame should bring up Shadowbox.

        $('.img-gallery').each(function () {
            var gallery = this;
            var gallery_type = $(this).attr('data-gallery-type');

            if (gallery_type !== undefined && gallery_type === 'link') {
                // For a "link"-type gallery, also update a caption.
                $(gallery).children('.img-container').on('onSeek',
                    function(event, index) {
                        var $items = $(this).data('scrollable').getItems();
                        var a = $items[index];
                        $('.img-gallery .plant-name').text(a.title);
                        var is_scientific_name = ($(a).attr(
                            'data-is-scientific-name') === 'true');
                        $('.img-gallery .plant-name').toggleClass(
                            'scientific', is_scientific_name);
                    }
                );
            }

            $(gallery).click(function () {
                var container;
                var photo_helper = PhotoHelper();
                if ($('body#species').length > 0) {
                    // species page: deeper HTML structure created by scroller
                    container = $(gallery).find('.scrollWrapper');
                }
                else {
                    container = $(gallery).children('.img-container');
                }

                var scroll = container.data('scrollable');
                var a = scroll.getItems()[scroll.getIndex()];

                if (gallery_type !== undefined && gallery_type === 'link') {
                    // "Link" gallery: simple hyperlink on image
                    if (a !== undefined) {
                        window.location.href = $(a).attr('href');
                    }
                }
                else {
                    // Default gallery type: lightboxed plant photo
                    var rel = $(a).attr('rel');
                    var title = $(a).attr('title');
                    var galleryname = rel.split('[')[1].split(']')[0];

                    // Before opening, ensure Shadowbox has the necessary
                    // event handlers.
                    // This serves most uses of the gallery, except for the
                    // auto-scrolling area on species pages, which need
                    // extra initialization for these event handlers.
                    Shadowbox.setup('.img-gallery .images a', {
                        onOpen: photo_helper.prepare_to_enlarge,
                        onChange: photo_helper.prepare_to_enlarge,
                        onFinish: photo_helper.process_credit
                    });

                    Shadowbox.open({
                        content: a,
                        gallery: galleryname,
                        player: 'img',
                        title: title,
                        options: {
                            counterType: 'skip'
                        }
                    });
                }
            });
        });
    };

    // Return the constructor function.
    return ImageGallery;
});

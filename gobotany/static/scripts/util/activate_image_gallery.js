/*
 * Activate any class="img-container" elements to make them scrollable
 * using their "prev" and "next" buttons.
 */

require([
    'bridge/jquery',
    'bridge/jquery.mousewheel',
    'bridge/shadowbox',
    'util/PhotoHelper'
], function ($, mousewheel, Shadowbox, PhotoHelper) {
    $(document).ready(function () {

        // Turn on the scrollable for every gallery.

        $('.img-container').scrollable({keyboard: false});

        // For each gallery, clicking its frame should bring up Shadowbox.

        $('.img-gallery').each(function() {
            var gallery = this;
            var gallery_type = $(this).attr('data-gallery-type');
            var photo_helper = PhotoHelper();

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

            $(gallery).children('.frame').click(function () {
                var container = $(gallery).children('.img-container');
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

    });
});

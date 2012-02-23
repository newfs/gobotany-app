/*
 * Activate any class="img-container" elements to make them scrollable
 * using their "prev" and "next" buttons.
 */

require([
    'jquery.tools.min',
    'dojo_config',
    '/static/js/dojo/dojo.js',
    '/static/js/layers/sk.js',
    'sidebar'
], function() {

  require([
      'jquery.mousewheel.min'
  ], function() {

    dojo.require('gobotany.sk.photo');

    $(document).ready(function() {

        // Turn on the scrollable for every gallery.

        $('.img-container').scrollable({keyboard: false});

        // For each gallery, clicking its frame should bring up Shadowbox.

        $('.img-gallery').each(function() {
            var gallery = this;
            var photo_helper = gobotany.sk.photo.PhotoHelper();
            $(gallery).children('.frame').click(function() {
                var container = $(gallery).children('.img-container');
                var scroll = container.data('scrollable');
                var a = scroll.getItems()[scroll.getIndex()];
                var rel = $(a).attr('rel');
                var title = $(a).attr('title');
                var galleryname = rel.split('[')[1].split(']')[0];
                Shadowbox.open({
                    content: a,
                    gallery: galleryname,
                    player: 'img',
                    title: title,
                    options: {
                        counterType: 'skip',
                        onOpen: photo_helper.prepare_to_enlarge,
                        onChange: photo_helper.prepare_to_enlarge,
                        onFinish: photo_helper.process_title_and_credit
                    }
                });
                /* TODO: Find out why when the gallery option is
                 * supplied, none of the onOpen, onChange, or onFinish
                 * hooks are firing, preventing us from being able to
                 * format our photo title and credit. Removing the
                 * gallery option allows the hooks to fire, but no
                 * longer shows multiple items in a gallery, just the
                 * first item. The Shadowbox forum is at:
                 * http://shadowbox-js.1309102.n2.nabble.com/
                 */
            });
        });

    });
  });
});

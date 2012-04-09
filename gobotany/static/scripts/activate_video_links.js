/* Activate any video links to make them open in a lightbox. */

require([
    'jquery.tools.min',
    'shadowbox',
    'shadowbox_init'
], function() {
    $(document).ready(function() {
        $('a.video').click(function() {
            // Work around a bug when using lightboxes on iPad:
            // On iOS 5, videos do not start playing if the page is
            // scrolled down, so scroll to the top.
            if (navigator.userAgent.match(/(iPad)/)) {
                if (navigator.userAgent.match(/(OS 5_)/) &&
                    this.href.indexOf('youtube.com') > -1) {

                    window.scrollTo(0, 0);
                }
            }

            Shadowbox.open({
                content: this.href,
                player: "iframe"
            });
            return false;
        });
    });
});


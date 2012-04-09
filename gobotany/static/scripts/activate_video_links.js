/* Activate any video links to make them open in a lightbox. */

require([
    'jquery.tools.min',
    'shadowbox',
    'shadowbox_init'
], function() {
    $(document).ready(function() {
        $('a.video').click(function() {
            // Work around a bug when using lightboxes on iPad:
            // Videos do not start playing if the page is scrolled down,
            // so scroll to the top.
            if (navigator.userAgent.match(/(iPad)/)) {
                if (this.href.indexOf('youtube.com') > -1) {
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


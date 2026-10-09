/* Activate any video links to make them open in a lightbox. */

require([
    'bridge/jquery',
    'bridge/shadowbox',
    'util/shadowbox_init'
], function ($, Shadowbox, shadowbox_init) {
    $(document).ready(function () {
        $('button.video').each(function () {
            // Open the video in a lightbox.
            var link = this;
            $(this).click(function () {
                let href = link.dataset.href;
                if (href) {
                    Shadowbox.open({
                        content: href,
                        player: "iframe"
                    });
                }
            });
        });
    });
});

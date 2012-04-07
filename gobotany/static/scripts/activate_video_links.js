/* Activate any video links to make them open in a lightbox. */

require([
    'jquery.tools.min',
    'shadowbox',
    'shadowbox_close'
], function() {
    $(document).ready(function() {
        $('a.video').click(function() {
            Shadowbox.open({
                content: this.href,
                player: "iframe"
            });
            return false;
        });
    });
});


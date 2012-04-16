/* Activate any video links to make them open in a lightbox. */

require([
    'jquery.tools.min',
    'shadowbox',
    'shadowbox_init'
], function() {
    $(document).ready(function() {
        $('a.video').each(function() {
            // On iOS, instead of trying to use the lightbox for videos
            // (due to buggy behavior that requires scrolling to the top),
            // use a link that will open in the device's YouTube app.
            if (navigator.userAgent.match(/(iPad|iPod|iPhone)/)) {
                var start = this.href.lastIndexOf('/') + 1;
                var end = this.href.indexOf('?');
                var video_id = this.href.substring(start, end);
                var youtube_app_url = 'http://www.youtube.com/v/' + video_id;
                this.href = youtube_app_url;
            }
            else {
                // Open the video in a lightbox.
                var link = this;
                $(this).click(function() {
                    Shadowbox.open({
                        content: link.href,
                        player: "iframe"
                    });
                    return false;
                });
            }
        });
    });
});

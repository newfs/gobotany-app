require([
    'util/activate_video_links',
    'bridge/shadowbox',
    'util/shadowbox_init',
    'util/mailto'
], function(video_links, Shadowbox, shadowbox_init, mailto) {
    $(document).ready(function () {
        mailto.make_link('.email');
    });
});

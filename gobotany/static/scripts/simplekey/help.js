require([
    'util/activate_video_links',
    'bridge/shadowbox',
    'util/shadowbox_init',
    'util/sidebar',
    'util/mailto'
], function(video_links, Shadowbox, shadowbox_init, sidebar, mailto) {
    sidebar.setup();

    $(document).ready(function () {
        mailto.make_link('.email');
    });
});

require([
    'util/activate_video_links',
    'bridge/shadowbox',
    'util/shadowbox_init',
    'util/sidebar'
], function(video_links, Shadowbox, shadowbox_init, sidebar) {
    sidebar.setup()
});


require([
    'util/activate_search_suggest',
    'util/activate_video_links',
    'bridge/shadowbox',
    'util/shadowbox_init',
    'util/sidebar'
], function(Shadowbox, shadowbox_init, sidebar) {
    sidebar.setup()
});


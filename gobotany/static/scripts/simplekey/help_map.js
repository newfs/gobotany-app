require([
    'util/activate_search_suggest',
    'bridge/shadowbox',
    'util/shadowbox_init',
    'util/activate_video_links',
    'util/sidebar',
    'dojo/ready',
    'gobotany/sk/help'
], function(activate_search_suggest, Shadowbox, shadowbox_init, 
        activate_video_links, sidebar, ready, MapToGroupsHelper) {
    sidebar.setup()
    return ready(function() {
        var helper = new MapToGroupsHelper();
        helper.setup();
    });
});


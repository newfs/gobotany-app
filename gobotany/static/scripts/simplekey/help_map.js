require([
    'bridge/jquery',
    'util/activate_search_suggest',
    'util/activate_video_links',
    'util/shadowbox_init',
    'util/sidebar',
    'gobotany/sk/MapToGroupsHelper'
], function($, activate_search_suggest, activate_video_links, shadowbox_init,
    sidebar, MapToGroupsHelper) {

    sidebar.setup()
    $(document).ready(function() {
        var helper = MapToGroupsHelper();
        helper.setup();
    });
});


require([
    'bridge/jquery',
    'util/activate_video_links',
    'util/shadowbox_init',
    'util/sidebar',
    'simplekey/MapToGroupsHelper'
], function($, activate_video_links, shadowbox_init, sidebar,
            MapToGroupsHelper) {

    $(document).ready(function() {
        sidebar.setup();
        var helper = MapToGroupsHelper();
        helper.setup();
    });
});

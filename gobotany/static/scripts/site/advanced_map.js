require([
    'bridge/jquery',
    'util/activate_video_links',
    'util/shadowbox_init',
    'site/MapToGroupsHelper'
], function($, activate_video_links, shadowbox_init, MapToGroupsHelper) {

    $(document).ready(function() {
        var helper = MapToGroupsHelper();
        helper.setup();
    });
});

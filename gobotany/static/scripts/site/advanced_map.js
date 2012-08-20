require([
    'bridge/jquery',
    'util/activate_video_links',
    'util/shadowbox_init',
    'simplekey/MapToGroupsHelper'
], function($, activate_video_links, shadowbox_init, MapToGroupsHelper) {

    $(document).ready(function() {
        var helper = MapToGroupsHelper();
        helper.setup();
    });
});

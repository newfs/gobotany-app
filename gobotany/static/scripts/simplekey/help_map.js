require([
    'activate_search_suggest',
    'shadowbox',
    'shadowbox_init',
    'activate_video_links',
    'sidebar'
]);

require([
    'dojo/ready',
    'gobotany/sk/help'
], function(ready, MapToGroupsHelper) {
    return ready(function() {
        var helper = new MapToGroupsHelper();
        helper.setup();
    });
});


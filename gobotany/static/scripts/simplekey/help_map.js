require([
    'activate_search_suggest',
    'shadowbox',
    'shadowbox_init',
    'activate_video_links'
]);

require([
    'sidebar'
], function() {

    dojo.require('gobotany.sk.help');
    dojo.addOnLoad(function() {
      var helper = gobotany.sk.help.MapToGroupsHelper();
      helper.setup();
    });

});

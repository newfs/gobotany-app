require([
    'activate_search_suggest',
    'shadowbox',
    'shadowbox_init',
    'activate_video_links'
]);

require([
    'dojo_config',
    '/static/js/dojo/dojo.js',
    '/static/js/layers/sk.js',
    'sidebar'
], function() {

    dojo.require('gobotany.sk.help');
    dojo.addOnLoad(function() {
      var helper = gobotany.sk.help.MapToGroupsHelper();
      helper.setup();
    });

});

require([
    'activate_image_gallery',
    'activate_search_suggest',
    'shadowbox',
    'shadowbox_close'
]);

require([
    'dojo_config',
    '/static/js/dojo/dojo.js',
    '/static/js/layers/sk.js',
    'sidebar'
], function() {

    dojo.require('gobotany.sk.groups');
    dojo.addOnLoad(function() {
        var helper = gobotany.sk.groups.GroupsHelper();
        helper.setup();
    });

});

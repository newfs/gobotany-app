require([
    'activate_image_gallery',
    'shadowbox'
], function() {

    Shadowbox.init({
        onOpen: global_moveShadowboxCloseLink
    });

    dojo.require('gobotany.sk.groups');
    dojo.addOnLoad(function() {
        var helper = gobotany.sk.groups.GroupsHelper();
        helper.setup();
    });

});

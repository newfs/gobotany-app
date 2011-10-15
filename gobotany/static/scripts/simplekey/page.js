require([
    'dojo_config',
    '/static/js/dojo/dojo.js',
    '/static/js/layers/sk.js',

    'activate_image_gallery',
    'activate_search_suggest',
    'shadowbox'
], function() {

    Shadowbox.init({
        onOpen: function() {
            // Move the Shadowbox close link.
            var tb = document.getElementById('sb-wrapper');
            if (tb) tb.appendChild(document.getElementById('sb-nav-close'));
        }
    });

    dojo.require('gobotany.sk.groups');
    dojo.addOnLoad(function() {
        var helper = gobotany.sk.groups.GroupsHelper();
        helper.setup();
    });

});

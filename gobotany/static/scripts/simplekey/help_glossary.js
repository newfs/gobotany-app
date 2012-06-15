require([
    'util/activate_search_suggest',
    'bridge/shadowbox',
    'util/shadowbox_init',
    'util/sidebar',
    'simplekey/glossarize'
], function(activate_search_suggest, Shadowbox, shadowbox_init, sidebar, 
        glossarize) {
    sidebar.setup();
    $(document).ready(function() {
        glossarize($('#terms dd'));
    });
});


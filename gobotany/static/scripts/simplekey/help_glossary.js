require([
    'bridge/shadowbox',
    'util/shadowbox_init',
    'util/sidebar',
    'simplekey/glossarize'
], function(Shadowbox, shadowbox_init, sidebar, glossarize) {
    sidebar.setup();
    $(document).ready(function() {
        glossarize($('#terms dd'));
    });
});


require([
    'bridge/shadowbox',
    'util/shadowbox_init',
    'simplekey/glossarize'
], function(Shadowbox, shadowbox_init, glossarize) {
    $(document).ready(function() {
        glossarize($('#terms dd'));
    });
});


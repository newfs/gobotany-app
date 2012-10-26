require([
    'bridge/shadowbox',
    'util/glossarizer',
    'util/shadowbox_init'
], function(Shadowbox, glossarizer, shadowbox_init) {
    $(document).ready(function() {
        glossarizer.glossarize($('#terms dd'));
    });
});

require([
    'activate_search_suggest',
    'bridge/shadowbox',
    'util/shadowbox_init',
    'sidebar'
]);

require([
    'simplekey/glossarize'
], function(glossarize) {
    $(document).ready(function() {
        glossarize($('#terms dd'));
    });
});

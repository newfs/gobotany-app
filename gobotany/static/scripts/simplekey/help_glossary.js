require([
    'activate_search_suggest',
    'shadowbox',
    'shadowbox_init',
    'sidebar'
]);

require([
    'simplekey/glossarize'
], function(glossarize) {
    $(document).ready(function() {
        glossarize($('#terms dd'));
    });
});

require([
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

    dojo.require('gobotany.sk.glossary');
    dojo.addOnLoad(function() {
        glossary_helper = gobotany.sk.glossary.GlossaryHelper();
        glossary_helper.setup();
    });

});

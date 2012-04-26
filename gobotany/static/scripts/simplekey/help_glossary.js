require([
    'activate_search_suggest',
    'shadowbox',
    'shadowbox_init'
]);

require([
    'dojo_config',
    '/static/js/dojo/dojo.js',
    '/static/js/layers/sk.js',
    'lib/tooltipsy',
    'sidebar'
], function() {

    dojo.require('gobotany.sk.glossary');

dojo.declare('gobotany.sk.glossary.GlossaryHelper', null, {
    constructor: function() {
        this.glossarizer = new gobotany.sk.glossary.Glossarizer();
    },
    setup: function() {
        var glossarizer = this.glossarizer;
        $('#terms dd').each(function(i, node) {
            glossarizer.markup(node);
        });
    }
});


    dojo.addOnLoad(function() {
        glossary_helper = gobotany.sk.glossary.GlossaryHelper();
        glossary_helper.setup();
    });

});

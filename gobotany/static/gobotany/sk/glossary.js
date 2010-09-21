dojo.provide('gobotany.sk.glossary');
dojo.require('gobotany.sk.glossarize');

dojo.declare('gobotany.gloassary.GlossaryHelper', null, {
    constructor: function() {
        this.glossarizer = new gobotany.sk.results.Glossarizer();
    },
    setup: function() {
        var glossarizer = this.glossarizer;
        dojo.query('#glossary .definition').forEach(function(node) {
            glossarizer.markup(node);
        });
    });
    }
});

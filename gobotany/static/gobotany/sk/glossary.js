// Global declaration for JSLint (http://www.jslint.com/)
/*global dojo, gobotany */

dojo.provide('gobotany.sk.glossary');
dojo.require('gobotany.sk.glossarize');

dojo.declare('gobotany.sk.glossary.GlossaryHelper', null, {
    constructor: function() {
        this.glossarizer = new gobotany.sk.results.Glossarizer();
    },
    setup: function() {
        var glossarizer = this.glossarizer;
        dojo.query('#glossary .definition').forEach(function(node) {
            glossarizer.markup(node);
        });
    }
});

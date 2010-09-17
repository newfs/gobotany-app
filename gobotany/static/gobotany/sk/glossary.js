dojo.provide('gobotany.sk.glossary');
dojo.require('gobotany.sk.glossarize');

dojo.addOnLoad(function() {
    var glossarizer = new gobotany.sk.results.Glossarizer();

    dojo.query('#glossary .definition').forEach(function(node) {
        glossarizer.markup(node);
    });
});

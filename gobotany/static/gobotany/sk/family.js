dojo.provide('gobotany.sk.family');

dojo.require('gobotany.sk.glossarize');

gobotany.sk.family.init = function() {
    // Make glossary highlights appear where appropriate throughout the page.
    var glossarizer = gobotany.sk.results.Glossarizer();
    dojo.query('#info p').forEach(function(node) {
        glossarizer.markup(node);
    });
}

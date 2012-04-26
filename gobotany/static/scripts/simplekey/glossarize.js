define([
    'simplekey/Glossarizer',
    'simplekey/resources'
], function(Glossarizer, resources) {

    var glossarizer = null;
    var ready = $.Deferred();

    resources.glossaryblob().done(function(blob) {
        glossarizer = Glossarizer.create({
            glossaryblob: blob
        });
        ready.resolve();
    });

    return function($nodes) {
        ready.done(function() {
            $nodes.each(function(i, node) {
                glossarizer.markup(node);
            });
        });
    }
});

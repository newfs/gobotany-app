// Global declaration for JSLint (http://www.jslint.com/)
/*global dojo, dojox, dijit, gobotany */

dojo.provide('gobotany.sk.glossary');

escapeRegExp = function(str) {
    // http://stackoverflow.com/questions/3446170/
    return str.replace(/[-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g, '\\$&');
};

dojo.declare('gobotany.sk.glossary.GlossaryHelper', null, {
    constructor: function() {
        this.glossarizer = new gobotany.sk.glossary.Glossarizer();
    },
    setup: function() {
        var glossarizer = this.glossarizer;
        dojo.query('#terms dd').forEach(function(node) {
            glossarizer.markup(node);
        });
    }
});

dojo.declare('gobotany.sk.glossary.Glossarizer', null, {

    /* The glossarizer downloads the glossary blob, parses and prepares
       its data, then fires off its .ready Deferred so that .markup()
       can run. */

    constructor: function() {
        this.n = 0;
        this.ready = $.Deferred();
        simplekey_resources.glossaryblob().done($.proxy(this, 'parse'));
    },

    parse: function(glossaryblob) {
        this.glossaryblob = glossaryblob;

        var terms = [];
        var defs = this.glossaryblob.definitions;
        for (term in defs)
            if (defs.hasOwnProperty(term))
                terms.push(escapeRegExp(term));

        /* For incredible speed, we pre-build a regular expression of
           all glossary terms.  This has the advantage of always selecting
           the longest possible glossary term if several words together
           could be a glossary term! */
        var re = '\\b(' + terms.join('|') + ')\\b';
        this.regexp = new RegExp(re, 'gi');

        this.ready.resolve();
    },

    /* Call "markup" on a node - hopefully one with no elements
       beneath it, but just text - to have its innerHTML scanned for
       glossary terms.  Any terms found are replaced with a <span>
       to which a Dijit tooltip is then attached. */

    markup: function(node) {
        this.ready.done(_.bind(function() {
            node.innerHTML = node.innerHTML.replace(
                this.regexp, '<span class="gloss">$1</span>'
            );
            var self = this;
            var defs = this.glossaryblob.definitions;
            var images = this.glossaryblob.images;
            dojo.query('.gloss', node).forEach(function(node2) {
                self.n++;
                var gloss_id = 'gloss' + self.n;
                var term = node2.innerHTML.toLowerCase();
                var imgsrc = images[term];
                node2.id = gloss_id;
                $('#' + gloss_id).tooltipsy({
                    content: '<p class="glosstip">' +
                        (imgsrc ? '<img src="' + imgsrc + '">' : '') +
                        defs[term] + '</p>'
                });
            });
        }, this));
    }
});

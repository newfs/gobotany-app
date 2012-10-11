define([
    'bridge/ember',
    'bridge/jquery',
    'util/tooltip'
], function(Ember, $, tooltip) {return Ember.Object.extend({

    /* The glossarizer takes the glossary blob delivered by the API,
       parses and prepares a regular expression, and then can mark up
       glossary terms inside of text so that they turn into tooltipped
       terms. */

    _escape: function(str) {
        // http://stackoverflow.com/questions/3446170/
        return str.replace(/[-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g, '\\$&');
    },

    init: function() {
        // this.glossaryblob must be provided in create()
        this.n = 0;
        var terms = [];
        var defs = this.glossaryblob.definitions;
        for (term in defs)
            if (_.has(defs, term))
                terms.push(this._escape(term));

        /* For incredible speed, we pre-build a regular expression of
           all glossary terms.  This has the advantage of always selecting
           the longest possible glossary term if several words together
           could be a glossary term! */
        var re = '\\b(' + terms.join('|') +
            ')([\\+\\-]|\\b)'; // Allow + or - at end: wetland indicator codes
        this.regexp = new RegExp(re, 'gi');
    },

    /* Call "markup" on a node - hopefully one with no elements beneath
       it, but just text - to have its text scanned for glossary terms.
       Any terms found are replaced with a <span> to which a tooltip is
       then attached. */

    markup: function(node) {

        /* Place any glossary terms in the node inside spans. */

        var self = this;
        var TEXT_NODE = 3;

        $(node).contents().each(function() {
            if (this.nodeType === TEXT_NODE)
                $(this).replaceWith(_.escape(this.textContent).replace(
                    self.regexp, '<span class="gloss">$1$2</span>'));
        });

        /* Attach the new spans to tooltips. */

        var defs = this.glossaryblob.definitions;
        var images = this.glossaryblob.images;

        $('.gloss', node).each(function(i, span) {
            self.n++;
            var gloss_id = 'gloss' + self.n;
            var term = span.innerHTML.toLowerCase();
            var imgsrc = images[term];
            span.id = gloss_id;

            var definition = defs[term];
            if (definition === undefined) {
                // If the definition was not found, try looking it up
                // without converting the term to lowercase. This will
                // allow finding all-uppercase terms (ex.: the wetland
                // indicator code FACW). Converting the term to lower case
                // is still desirable as the default because it allows
                // markup of terms that appear in mixed case on the pages.
                definition = defs[span.innerHTML];
            }

            $(span).tooltip({
                content: '<p class="glosstip">' +
                    (imgsrc ? '<img src="' + imgsrc + '">' : '') +
                    definition + '</p>'
            });
        });
    }
})});

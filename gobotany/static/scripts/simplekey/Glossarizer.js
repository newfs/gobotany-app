define([
    'ember',
    'bridge/jquery',
    'lib/tooltipsy'
], function() {return Ember.Object.extend({

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

    /* Call "markup" on a node - hopefully one with no elements
       beneath it, but just text - to have its innerHTML scanned for
       glossary terms.  Any terms found are replaced with a <span>
       to which a Dijit tooltip is then attached. */

    markup: function(node) {
        node.innerHTML = node.innerHTML.replace(
            this.regexp, '<span class="gloss">$1$2</span>'
        );
        var self = this;
        var defs = this.glossaryblob.definitions;
        var images = this.glossaryblob.images;
        $('.gloss', node).each(function(i, node2) {
            self.n++;
            var gloss_id = 'gloss' + self.n;
            var term = node2.innerHTML.toLowerCase();
            var imgsrc = images[term];
            node2.id = gloss_id;
            
            var definition = defs[term];
            if (definition === undefined) {
                // If the definition was not found, try looking it up
                // without converting the term to lowercase. This will
                // allow finding all-uppercase terms (ex.: the wetland
                // indicator code FACW). Converting the term to lower case
                // is still desirable as the default because it allows
                // markup of terms that appear in mixed case on the pages.
                definition = defs[node2.innerHTML];
            }

            $('#' + gloss_id).tooltipsy({
                content: '<p class="glosstip">' +
                    (imgsrc ? '<img src="' + imgsrc + '">' : '') +
                    definition + '</p>',
                show: function(event, $tooltip) {
                    if (parseFloat($tooltip.css('left')) < 0)
                        $tooltip.css('left', '0px');
                    $tooltip.show();
                }
            });
        });
    }
})});

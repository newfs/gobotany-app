define([
    'bridge/jquery',
    'bridge/underscore',
    'simplekey/resources',
    'util/tooltip'
], function($, _, resources, tooltip) {

    var exports = {};

    /* Escape a string for literal use in a regular expression. */

    exports.escape = function(str) {
        // http://stackoverflow.com/questions/3446170/
        return str.replace(/[-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g, '\\$&');
    };

    /* Special terms we want to avoid escaping. */

    var avoid_terms = ['Fern.'];

    /* The glossarizer takes a glossary blob as delivered by the API,
       parses and prepares a regular expression, and then can mark up
       glossary terms inside of text so that they turn into tooltipped
       terms. */

    exports.Glossarizer = function(glossaryblob) {
        this.glossaryblob = glossaryblob;
        this.n = 0;

        var terms = [];

        /* Build a list of escaped regular expressions for each term. */

        _.each(avoid_terms, function(term) {
            terms.push(exports.escape(term));
        });

        _.each(glossaryblob.definitions, function(definition, term) {
            var eterm = exports.escape(term);

            /* Lower-case terms can also start with an upper-case letter. */

            if (/^[a-z]/.test(eterm)) {
                var e0 = '[' + eterm[0] + eterm[0].toUpperCase() + ']';
                var rest = eterm.slice(1);
                eterm = e0 + rest;
            }

            /* Terms that end with a letter should end at a word boundary. */

            if (/\w$/.test(eterm)) {
                eterm = eterm + '\\b';
            }

            terms.push(eterm);
        });

        /* For incredible speed, we pre-build a regular expression of
           all glossary terms.  This has the advantage of always selecting
           the longest possible glossary term if several words together
           could be a glossary term! */

        var re = '\\b(' + terms.join('|') + ')';
        this.regexp = new RegExp(re, 'g');
    },

    /* Call "markup" on a node - hopefully one with no elements beneath
       it, but just text - to have its text scanned for glossary terms.
       Any terms found are replaced with a <span> to which a tooltip is
       then attached. */

    exports.Glossarizer.prototype.markup = function(node, terms_section) {

        /* Place any glossary terms in the node inside spans. */

        var self = this;
        var TEXT_NODE = 3;

        var replacer = function(match, term) {
            if (_.contains(avoid_terms, term))
                return match;
            else
                return '<span class="gloss">' + match + '</span>';
        };

        $(node).contents().each(function() {
            if (this.nodeType !== TEXT_NODE)
                return;
            $(this).replaceWith(
                _.escape(this.textContent).replace(self.regexp, replacer)
            );
        });

        var defs = this.glossaryblob.definitions;

        if (terms_section === undefined) {
            /* Attach the new spans to tooltips. */

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
        else {
            /* Add this node's terms to a list that can be shown on small
               screens. */

            var terms_list = terms_section + ' ul';
            $('.gloss', node).each(function(i, span) {
                var term = span.innerHTML.toLowerCase();

                // List a term unless it has already been listed.
                var is_already_listed =
                    $(terms_list).find('li').hasClass(term);
                if (!is_already_listed) {
                    $(terms_list).append('<li class="' + term + '"><span>' +
                        term + ':</span> ' + defs[term] + '</li>');
                    // Signal that the list has at least one term.
                    $(terms_section).removeClass('none');
                }
            });
        }
    };

    /* Convenience routine that glossarizes elements as soon as the
       glossary blob has arrived from the API.
       
       An optional argument 'terms_section' can be passed, which adds the
       terms and definitions to a list instead of making tooltips. */

    var glossarizer = null;
    var kickoff = $.Deferred();
    var ready = $.Deferred();

    kickoff.done(function() {
        resources.glossaryblob().done(function(blob) {
            glossarizer = new exports.Glossarizer(blob);
            ready.resolve();
        });
    });

    exports.glossarize = function($nodes, terms_section) {
        kickoff.resolve();
        ready.done(function() {
            $nodes.each(function(i, node) {
                glossarizer.markup(node, terms_section);
            });
        });
    };

    return exports;
});

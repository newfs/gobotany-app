// Global declaration for JSLint (http://www.jslint.com/)
/*global dojo, dojox, dijit */

dojo.provide('gobotany.sk.glossarize');
dojo.require("dojo.regexp");
dojo.require('dojox.data.JsonRestStore');
dojo.require("dijit.Tooltip");

dojo.declare('gobotany.sk.results.Glossarizer', null, {

    /* The glossarizer downloads the glossary blob - the glossary
       represented as a single JavaScript object - synchronously
       because I am not quite sure how to batch up requests for
       glossarization and then do them all once the glossary blob
       arrives. */

    constructor: function() {
        this.n = 0;
        this.store = new dojox.data.JsonRestStore({
            target: '/glossaryblob/',
            syncMode: true
        });
        this.glossaryblob = this.store.fetch().results;
        var terms = [];
        for (var i = 0; i < this.glossaryblob.length; i++) {
            terms.push(dojo.regexp.escapeString(terms[i]));
        }
        /* For incredible speed, we pre-build a regular expression of
           all glossary terms.  This has the incredible advantage of
           always selecting the longest possible glossary term if
           several words together could be a glossary term! */
        var re = '\\b(' + terms.join('|') + ')\\b';
        this.regexp = new RegExp(re, 'gi');
    },

    /* Call "markup" on a node - hopefully one with no elements
       beneath it, but just text - to have its innerHTML scanned for
       glossary terms.  Any terms found are replaced with a <span>
       to which a Dijit tooltip is then attached. */

    markup: function (node) {
        node.innerHTML = node.innerHTML.replace(
            this.regexp, '<span class="gloss">$1</span>'
        );
        var gize = this;
        dojo.query('.gloss', node).forEach(function (node2) {
            gize.n++;
            var gloss_id = 'gloss' + gize.n;
            node2.id = gloss_id;
            dijit.Tooltip({
                connectId: [ gloss_id ],
                label: '<span class="glosstip">' + gize.glossaryblob[
                    node2.innerHTML] + '</span>',
                position: 'above'
            });
        });
    }
});


dojo.provide('gobotany.sk.glossarize');
dojo.require("dojo.regexp");
dojo.require('dojox.data.JsonRestStore');
dojo.require("dijit.Tooltip");

dojo.declare('gobotany.sk.results.Glossarizer', null, {
    constructor: function() {
        this.n = 0;
        this.store = new dojox.data.JsonRestStore({
            target: '/glossaryblob/',
            syncMode: true,
        });
        this.glossaryblob = this.store.fetch().results;
        var terms = new Array();
        for (term in this.glossaryblob) {
            terms.push(term);
        }
        var re = '\\b(' + terms.join('|') + ')\\b';
        this.regexp = new RegExp(re, 'gi');
    },
    markup: function (node) {
        node.innerHTML = node.innerHTML.replace(
            this.regexp, '<span class="gloss">$1</span>'
        );
        var gize = this;
        dojo.query('.gloss', node).forEach(function (node2) {
            gize.n ++;
            var gloss_id = 'gloss' + gize.n;
            node2.id = gloss_id;
            new dijit.Tooltip({
                connectId: [ gloss_id ],
                label: '<span class="glosstip">' + gize.glossaryblob[
                    node2.innerHTML] + '</span>',
                position: 'above',
            });
        });
    },
})

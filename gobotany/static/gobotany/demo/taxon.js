dojo.provide('gobotany.demo.taxon');
dojo.require('dojox.data.JsonRestStore');

gobotany.demo.taxon._base_url = '/taxon';

dojo.declare('gobotany.demo.taxon.TaxonHelper', null, {
    constructor: function(args) {
        this.taxon_store = new dojox.data.JsonRestStore({target: gobotany.demo.taxon._base_url});
    },

    init: function() {
        console.log('Setting up TaxonHelper');
        this.populate_taxon_select();
        var s = dojo.byId('taxon_select');
        dojo.connect(s, 'onchange', null,
                     dojo.hitch(this, this.populate_results));
    },

    populate_taxon_select: function() {
        var s = dojo.byId('taxon_select');
        var store = this.taxon_store;
        store.fetch({
            scope: this,
            onComplete: function(res) {
                dojo.empty(s);
                for (var x = 0; x < res.items.length; x++) {
                    var n = res.items[x].scientific_name;
                    dojo.place('<option value="'+n+'">'+n+'</option>', s);
                }
                s.disabled = false;
            }});
    },

    populate_results: function() {
        var s = dojo.byId('taxon_select');
        var d = dojo.byId('taxon_results');
        dojo.empty(d);
        var species = s.options[s.selectedIndex].value;
        var store = this.taxon_store;
        store.fetch({
            query: {scientific_name: species},
            scope: this,
            onComplete: function(res) {
                for (var x = 0; x < res.items.length; x++) {
                    var dl = dojo.place('<dl></dl>', d);
                    for (y in res.items[0]) {
                        dojo.place('<dt>'+y+'</dt>', dl);
                        dojo.place('<dd>'+res.items[0][y]+'</dd>', dl);
                    }
                }
            }});
    }
});

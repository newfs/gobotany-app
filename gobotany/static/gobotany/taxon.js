dojo.provide('gobotany.taxon');
dojo.require('dojox.data.JsonRestStore');

gobotany.taxon._base_url = '/taxon';
gobotany.taxon._taxon_store = new dojox.data.JsonRestStore({target: gobotany.taxon._base_url});

gobotany.taxon.populate_taxon_select = function() {
    var s = dojo.byId('taxon_select');
    var store = gobotany.taxon._taxon_store;
    store.fetch({onComplete: function(res) {
        for (var x = 0; x < res.items.length; x++) {
            var n = res.items[x].scientific_name;
            dojo.place('<option value="'+n+'">'+n+'</option>', s);
        }
    }});
};

gobotany.taxon.populate_results = function() {
    var s = dojo.byId('taxon_select');
    var d = dojo.byId('taxon_results');
    dojo.empty(d);
    var species = s.options[s.selectedIndex].value;
    var store = gobotany.taxon._taxon_store;
    store.fetch({query: {scientific_name: species}, onComplete: function(res) {
        for (var x = 0; x < res.items.length; x++) {
            var dl = dojo.place('<dl></dl>', d);
            for (y in res.items[0]) {
                dojo.place('<dt>'+y+'</dt>', dl);
                dojo.place('<dd>'+res.items[0][y]+'</dd>', dl);
            }
        }
    }});
};


gobotany.taxon.init = function() {
    gobotany.taxon.populate_taxon_select();
    var s = dojo.byId('taxon_select');
    dojo.connect(s, 'onchange', null, gobotany.taxon.populate_results);
};

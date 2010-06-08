dojo.provide('gobotany.piles');
dojo.require('dojox.data.JsonRestStore');

gobotany.piles._taxon_count_store = new dojox.data.JsonRestStore({target: '/taxon-count'});

gobotany.piles.init = function() {
    var f = dojo.byId('characters_form');
    var b = dojo.place('<input type="button" value="Check Counts">', f);
    var d = dojo.place('<span></span>', f);
    dojo.connect(b, 'onclick', function() {
        var obj = dojo.formToObject(f);
        dojo.empty(d);
        gobotany.piles._taxon_count_store.fetch({query: obj, onComplete: function(res) {
            d.innerHTML = dojo.objectToQuery(res);
        }});
    });
};

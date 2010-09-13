dojo.provide('gobotany.demo.piles');
dojo.require('dojox.data.JsonRestStore');

gobotany.demo.piles.init = function() {
    var f = dojo.byId('characters_form');
    var b = dojo.place('<input type="button" value="Check Counts">', f);
    var d = dojo.place('<span></span>', f);
    dojo.connect(b, 'onclick', function() {
        var obj = dojo.formToObject(f);
        delete obj['csrfmiddlewaretoken'];
        var todel = [];
        for (var x in obj) {
            if (obj[x] == '')
                delete obj[x];
        }

        dojo.empty(d);
        var taxon_count_store = new dojox.data.JsonRestStore({target: '/taxon-count'});

        taxon_count_store.fetch({query: obj, onComplete: function(res) {
            var dl = dojo.place('<dl></dl>', d);
            dojo.place('<dt>Matched</dt>', dl);
            dojo.place('<dd>'+res.matched+'</dd>', dl);
            dojo.place('<dt>Excluded</dt>', dl);
            dojo.place('<dd>'+res.excluded+'</dd>', dl);
        }});
    });
};

gobotany.demo.piles._populate_base_pile_listing = function(basename) {
    var select = dojo.byId(basename+'-select');
    var store = new dojox.data.JsonRestStore({target: '/'+basename+'s/'});
    store.fetch({onComplete: function(res) {
        dojo.empty(select);
        for (var x = 0; x < res.items.length; x++) {
            var item = res.items[x];
            dojo.place('<option value="'+item.resource_uri+'">'+item.name+'</option>', select);
        }
        select.disabled = false;
    }});
};

gobotany.demo.piles.populate_piles = function() {
    gobotany.demo.piles._populate_base_pile_listing('pile');
};

gobotany.demo.piles.populate_pile_groups = function() {
    gobotany.demo.piles._populate_base_pile_listing('pilegroup');
};

gobotany.demo.piles._show_base_pile_info = function(basename, uri) {
    var store = new dojox.data.JsonRestStore({target: '/'+basename+'s/'});
    store.fetchItemByIdentity({identity: uri, onItem: function(item) {
        var dl = dojo.byId(basename+'-info');
        dojo.empty(dl);
        for (var x in item) {
            if (x[0] != '_') {
                dojo.place('<dt>'+x+'</dt>', dl);
                dojo.place('<dd>'+item[x]+'</dd>', dl);
            }
        }
    }});
};

gobotany.demo.piles.show_pile = function(uri) {
    gobotany.demo.piles._show_base_pile_info('pile', uri);
};

gobotany.demo.piles.show_pilegroup = function(uri) {
    gobotany.demo.piles._show_base_pile_info('pilegroup', uri);
};

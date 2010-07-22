dojo.provide('gobotany.piles');
dojo.require('dojox.data.JsonRestStore');

gobotany.piles._taxon_count_store = new dojox.data.JsonRestStore({target: '/taxon-count'});

gobotany.piles.init = function() {
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
        gobotany.piles._taxon_count_store.fetch({query: obj, onComplete: function(res) {
            var dl = dojo.place('<dl></dl>', d);
            dojo.place('<dt>Matched</dt>', dl);
            dojo.place('<dd>'+res.matched+'</dd>', dl);
            dojo.place('<dt>Excluded</dt>', dl);
            dojo.place('<dd>'+res.excluded+'</dd>', dl);
        }});
    });
};


gobotany.piles._populate_base_pile_listing = function(basename) {
    var select = dojo.byId(basename+'-select');
    var store = new dojox.data.JsonRestStore({target: '/'+basename+'s/'});
    store.fetch({onComplete: function(res) {
        dojo.empty(select);
        for (var x = 0; x < res.items.length; x++) {
            var item = res.items[x];
            dojo.place('<option value="'+item.name+'">'+item.name+'</option>', select);
        }
        select.disabled = false;
    }});
};

gobotany.piles.populate_piles = function() {
    gobotany.piles._populate_base_pile_listing('pile');
};

gobotany.piles.populate_pile_groups = function() {
    gobotany.piles._populate_base_pile_listing('pilegroup');
};

gobotany.piles._show_base_pile_info = function(basename, name) {
    var store = new dojox.data.JsonRestStore({target: '/'+basename+'s/'});
    store.fetchItemByIdentity({identity: name, onItem: function(item) {
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

gobotany.piles.show_pile = function(name) {
    gobotany.piles._show_base_pile_info('pile', name);
};

gobotany.piles.show_pilegroup = function(name) {
    gobotany.piles._show_base_pile_info('pilegroup', name);
};

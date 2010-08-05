dojo.provide('gobotany.sk.simplekey_page');
dojo.require("dijit.Dialog");
dojo.require("dijit.form.Button");
dojo.require('dojox.embed.Flash');
dojo.addOnLoad(function() {
    dojo.query('.PileVideo').forEach(function (node, index, attr) {
        var path = dojo.attr(dojo.query('> a', node)[0], 'href');
        var player = new dojox.embed.Flash({path: path,
                                            width: 200,
                                            height: 200},
                                            node);
    });
});

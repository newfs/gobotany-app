dojo.provide('gobotany.sk.simplekey_page');
dojo.require('gobotany.sk.plant_preview');
dojo.require("dijit.Dialog");
dojo.require("dijit.TooltipDialog");
dojo.require("dijit.form.Button");
dojo.require("dijit.form.DropDownButton");
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

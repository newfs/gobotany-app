dependencies = {
    layers: [{
        name: '../layers/sk.js',
        dependencies: [
            'dijit.Dialog',
            'dijit.TitlePane',
            'dijit.Tooltip',
            'dijit.form.HorizontalRule',
            'dijit.form.HorizontalSlider',
            'dojox.data.JsonRestStore',
            'dojox.embed.Flash'
        ]
    }],
    prefixes: [
        ['layers', '../layers'],
        ['dijit', '../dijit'],
        ['dojox', '../dojox']
    ]
};

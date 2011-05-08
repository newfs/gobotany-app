dependencies = {
    layers: [{
        name: '../layers/sk.js',
        dependencies: [
            'dijit.Dialog',
            'dijit.TitlePane',
            'dijit.Tooltip',
            'dijit.form.Button',
            'dijit.form.CheckBox',
            'dijit.form.FilteringSelect',
            'dijit.form.Form',
            'dijit.form.HorizontalRule',
            'dijit.form.HorizontalRuleLabels',
            'dijit.form.HorizontalSlider',
            'dijit.form.Select',
            'dojo.cookie',
            'dojo.data.ItemFileWriteStore',
            'dojo.hash',
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

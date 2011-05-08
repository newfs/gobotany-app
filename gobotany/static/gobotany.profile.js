dependencies = {
    layers: [{
        name: '../layers/sklayer.js',
        /*resourceName: 'dojo.sklayer',*/
        /*layerDependencies: [
            'gobotany'
        ],*/
        dependencies: [
            'gobotany.sk.results'
        ]
    }],
    prefixes: [
        ['dijit', '../dijit'],
        ['dojox', '../dojox'],
        ['gobotany', '../../gobotany/src/gobotany/static/gobotany']
    ]
};

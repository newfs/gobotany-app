djConfig = {
    isDebug: false,
    debugAtAllCosts: false,
    useXDomain: false,
    baseUrl: '/static/js/dojo/',
    modulePaths: {
        gobotany: '/static/gobotany',
        layers: '/static/js/layers'
    },
    parseOnLoad: true
};

// New Dojo 1.7 global configuration object
// This must be loaded before the dojo AMD loader
dojoConfig = {
    isDebug: false,
    baseUrl: '/static/scripts',
    tlmSiblingOfDojo: false,
    async: false,
    packages: [
        { name: 'dojo', location: 'lib/dojo' },
        { name: 'dojox', location: 'lib/dojox' },
        { name: 'gobotany', location: '/static/gobotany' }
    ],
    // Until we fix the rest of the AMD modules
    // we need to leave this as true
    parseOnLoad: true
};


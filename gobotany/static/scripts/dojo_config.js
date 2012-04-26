djConfig = {
    isDebug: false,
    debugAtAllCosts: false,
    useXDomain: false,
    baseUrl: '/static/js/dojo/',
    modulePaths: {
        gobotany: '/static/gobotany',
        layers: '/static/js/layers'
    },
    parseOnLoad: true,
    // Config for 1.7, using backward compatibility config object
    async: false,
    packages: [
        { name: 'dojo', location: 'js/lib/dojo' },
        { name: 'dojox', location: 'js/lib/dojox' },
    ]
};

// New Dojo 1.7 global configuration object
// This must be loaded before the dojo AMD loader
dojoConfig = {
    isDebug: false,
    baseUrl: '/static/',
    // Use Legacy loader mode until we finish migration
    async: false,
    packages: [
        { name: 'dojo', location: 'js/lib/dojo' },
        { name: 'dojox', location: 'js/lib/dojox' },
    ],
};


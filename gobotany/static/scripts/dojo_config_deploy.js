// New Dojo 1.7 global configuration object
// This must be loaded before the dojo AMD loader
dojoConfig = {
    isDebug: false,
    baseUrl: '/static/build/scripts',
    tlmSiblingOfDojo: false,
    async: true,
    locale: 'en-us',
    packages: [
        { name: 'dojo', location: 'dojo' },
        { name: 'jquery', location: 'jquery' },
        { name: 'tools', location: 'tools' },
        { name: 'simplekey', location: 'simplekey' },
        { name: 'bridge', location: 'bridge' },
        { name: 'util', location: 'util' }
    ]
};


function copyOnly(mid) {
    return mid in {
        // There are no modules right now in gobotany that are copy-only. If
        // you have some, though, just add them here like this: 
        // 'app/module': 1
    };
}

function nonAMD(mid) {
    // These modules do NOT use AMD syntax 
    // and should be tagged as such
    return mid in {
        // There are no modules right now in gobotany that are non-AMD. If
        // you have some, though, just add them here like this: 
        // 'app/module': 1
    };
}

function legacyDojo(mid) {
    // Dojo modules which require legacy support - these have not
    // yet been converted to pure AMD syntax
    return mid in {
        'gobotany/sk/SpeciesSectionHelper':1,
        'gobotany/sk/family':1,
        'gobotany/sk/genus':1,
        'gobotany/sk/guided_search/Filter':1,
        'gobotany/sk/guided_search/Manager':1,
        'gobotany/sk/guided_search/SpeciesSectionHelper':1,
        'gobotany/sk/photo':1,
        'gobotany/sk/results':1,
        'gobotany/sk/species':1,
        'gobotany/sk/working_area':1
    };
}

var profile = {
    resourceTags: {
        // Files that contain test code.
        test: function (filename, mid) {
            return false;
        },

        // Files that should be copied as-is without being modified by the build system.
        copyOnly: function (filename, mid) {
            return copyOnly(mid);
        },

        // Files that are AMD modules.
        amd: function (filename, mid) {
            return /\.js$/.test(filename) && 
                !copyOnly(mid) && 
                !legacyDojo(mid) && 
                !nonAMD(mid);
        },

        miniExclude: function (filename, mid) {
            return false;
        }
    }
};


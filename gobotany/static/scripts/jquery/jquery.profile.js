function copyOnly(mid) {
    return mid in {
        // These are non-AMD complient modules, but they don't have legacy
        // Dojo in them so just mark them as copy-only, no need to modify them
    };
}

function nonAMD(mid) {
    // Modules which are not AMD modules and the build system needs to wrap
    // Currently, all jquery modules have been manually wrapped
    return mid in {
    };
}

function legacyDojo(mid) {
    // Dojo modules which require legacy support - these have not
    // yet been converted to pure AMD syntax
    return mid in {
    };
}

var profile = {
    // Indvidual files that are pretty much part of this
    // package even though they're not really in the right folder
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


function copyOnly(mid) {
    return mid in {
        // There are no modules right now in gobotany that are copy-only. If
        // you have some, though, just add them here like this: 
        // 'app/module': 1
    };
}

function nonAMD(mid) {
    // For the jQuery package, none of the scripts are currently AMD-complient modules,
    // so flag every module in the package as non-AMD.
    return true;
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


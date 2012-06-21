/* Configuration for Simple Key results page "Show photos of" menu items. */
define([], function() {
    var results_photo_menu = {
        "woody-angiosperms": {
            "default": "plant form",
            "omit": ["additional features", "stems"]
        },
        "woody-gymnosperms": {
            "default": "plant form",
            "omit": []
        },
        "non-thalloid-aquatic": {
            "default": "plant form",
            "omit": ["additional features", "detail of leaf and/or divisions",
                     "flowers and fruits", "leaf", "leaves and auricles",
                     "ligules", "shoots", "sori", "special features",
                     "spikelets", "spore cones", "spores", "stems and sheaths",
                     "vegetative leaves"]
        },
        "thalloid-aquatic": {
            "default": "plant form",
            "omit": []
        },
        "carex": {
            "default": "plant form",
            "omit": []
        },
        "poaceae": {
            "default": "plant form",
            "omit": ["flowers and fruits", "stems"]
        },
        "remaining-graminoids": {
            "default": "plant form",
            "omit": ["leaves", "special features", "stems"]
        },
        "orchid-monocots": {
            "default": "flowers",
            "omit": []
        },
        "non-orchid-monocots": {
            "default": "flowers",
            "omit": ["flowers and fruits", "special features", "stems"]
        },
        "monilophytes": {
            "default": "plant form",
            "omit": ["flowers and fruits", "inflorescences", "stems"]
        },
        "lycophytes": {
            "default": "plant form",
            "omit": ["flowers and fruits", "inflorescences", "leaves", "stems"]
        },
        "equisetaceae": {
            "default": "plant form",
            "omit": []
        },
        "composites": {
            "default": "flowers",
            "omit": []
        },
        "remaining-non-monocots": {
            "default": "flowers",
            "omit": ["additional features", "bark", "flowers and fruits",
                     "inflorescences", "special features", "winter buds"]
        }
    };
    return results_photo_menu;
});


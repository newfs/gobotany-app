/* Configuration for Simple Key results page "Show photos of" menu items. */
define([], function() {
    var results_photo_menu = {
        "woody-angiosperms": {
            "default": "plant form",
            "omit": ["additional features", "comparison", "stems"]
        },
        "woody-gymnosperms": {
            "default": "plant form",
            "omit": ["comparison"]
        },
        "non-thalloid-aquatic": {
            "default": "plant form",
            "omit": ["additional features", "comparison",
                     "detail of leaf and/or divisions",
                     "flowers and fruits", "leaf", "leaves and auricles",
                     "ligules", "shoots", "sori", "special features",
                     "spikelets", "spore cones", "spores",
                     "stems and sheaths", "vegetative leaves"]
        },
        "thalloid-aquatic": {
            "default": "plant form",
            "omit": ["comparison"]
        },
        "carex": {
            "default": "plant form",
            "omit": ["comparison"]
        },
        "poaceae": {
            "default": "plant form",
            "omit": ["comparison", "flowers and fruits", "stems"]
        },
        "remaining-graminoids": {
            "default": "plant form",
            "omit": ["comparison", "leaves", "special features", "stems"]
        },
        "orchid-monocots": {
            "default": "flowers",
            "omit": ["comparison"]
        },
        "non-orchid-monocots": {
            "default": "flowers",
            "omit": ["comparison", "flowers and fruits", "special features",
                     "stems"]
        },
        "monilophytes": {
            "default": "plant form",
            "omit": ["comparison", "flowers and fruits", "inflorescences",
            "stems"]
        },
        "lycophytes": {
            "default": "plant form",
            "omit": ["comparison", "flowers and fruits", "inflorescences",
                     "leaves", "stems"]
        },
        "equisetaceae": {
            "default": "plant form",
            "omit": ["comparison"]
        },
        "composites": {
            "default": "flowers",
            "omit": ["comparison"]
        },
        "remaining-non-monocots": {
            "default": "flowers",
            "omit": ["additional features", "bark", "comparison",
                     "flowers and fruits", "inflorescences",
                     "special features", "winter buds"]
        }
    };
    return results_photo_menu;
});


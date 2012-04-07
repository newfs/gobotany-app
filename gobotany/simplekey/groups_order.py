# Group and subgroup slugs in their proper display order for the Simple Key.

PILEGROUP_ORDER = dict((slug, i) for (i, slug) in enumerate([
    'woody-plants',
    'aquatic-plants',
    'graminoids',
    'monocots',
    'ferns',
    'non-monocots',
    ]))

PILE_ORDER = dict((slug, i) for (i, slug) in enumerate([
    'woody-angiosperms', 'woody-gymnosperms',
    'non-thalloid-aquatic', 'thalloid-aquatic',
    'carex', 'poaceae', 'remaining-graminoids',
    'orchid-monocots', 'non-orchid-monocots',
    'monilophytes', 'lycophytes', 'equisetaceae',
    'composites', 'remaining-non-monocots',
    ]))

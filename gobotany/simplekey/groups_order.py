from gobotany.core.models import PileGroup

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

def ordered_pilegroups():
    """Return all pile groups in display order."""
    return sorted(PileGroup.objects.all(),
                  key=lambda pg: PILEGROUP_ORDER[pg.slug])


def ordered_piles(pilegroup):
    """Return all piles for a pile group in display order."""
    return sorted(pilegroup.piles.all(),
                  key=lambda p: PILE_ORDER[p.slug])

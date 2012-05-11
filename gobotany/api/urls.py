from django.conf import settings
from django.conf.urls.defaults import patterns, url
from django.contrib import admin
from django.views.decorators.cache import cache_control, cache_page

from gobotany.api import handlers, views
from piston.resource import Resource

admin.autodiscover()

handler500 = 'django.views.defaults.server_error'

urlpatterns = patterns(
    '',

    url(r'^taxon/(?P<scientific_name>[^/]+)/$',
        Resource(handler=handlers.TaxonQueryHandler), name='api-taxon'),
    url(r'^taxon/$',
        Resource(handler=handlers.TaxonQueryHandler), name='api-taxon-list'),
    # Suggested eventual replacement URL (plural) for /taxon/ above:
    url(r'^taxa/(?P<scientific_name>[^/]+)/$',
        Resource(handler=handlers.TaxonQueryHandler), name='api-taxa'),
    url(r'^taxa/$',
        Resource(handler=handlers.TaxonQueryHandler), name='api-taxa-list'),

    url(r'^taxon-count/$',
        Resource(handler=handlers.TaxonCountHandler), name='api-taxon-count'),
    # Suggested eventual replacement URL (plural) for /taxon-count/ above:
    url(r'^taxa-count/$',
        Resource(handler=handlers.TaxonCountHandler), name='api-taxa-count'),

    url(r'^taxon-image/$',
        Resource(handler=handlers.TaxonImageHandler), name='api-taxon-image'),

    url(r'^characters/$',
        Resource(handler=handlers.CharactersHandler)),
    url(r'^characters/(?P<character_short_name>[^/]+)/$',
        Resource(handler=handlers.CharacterHandler)),

    url(r'^piles/$',
        Resource(handler=handlers.PileListingHandler), name='api-pile-list'),

    # New-style API view (instead of one of the crufty old Handlers),
    # but which still needs to be listed up here because it needs to
    # take priority over the patterns that follow it:

    url(r'^piles/(?P<pile_slug>[^/]+)/characters/$',
        'gobotany.api.views.piles_characters',
        name='api-character-list'),

    #

    url(r'^piles/(?P<slug>[^/]+)/?$',
        Resource(handler=handlers.PileHandler), name='api-pile'),

    url(r'^piles/(?P<pile_slug>[^/]+)/(?P<character_short_name>[^/]+)/$',
        Resource(handler=handlers.CharacterValuesHandler),
        name='api-character-values'),

    url(r'^pilegroups/$',
        Resource(handler=handlers.PileGroupListingHandler),
        name='api-pilegroup-list'),
    url(r'^pilegroups/(?P<slug>[^/]+)/$',
        Resource(handler=handlers.PileGroupHandler), name='api-pilegroup'),

    # Plant distribution maps
    url(r'^maps/(?P<genus>[^/-]+)-(?P<specific_epithet>[^/]+)'
         '-ne-distribution-map(\.svg|/)?$',
        views.new_england_distribution_map, name='ne-distribution-map'),
    url(r'^maps/(?P<genus>[^/-]+)-(?P<specific_epithet>[^/]+)'
         '-na-distribution-map(\.svg|/)?$',
        views.north_american_distribution_map, name='na-distribution-map'),
    url(r'^maps/(?P<genus>[^/-]+)-(?P<specific_epithet>[^/]+)'
         '-us-distribution-map(\.svg|/)?$',
        views.united_states_distribution_map, name='us-distribution-map'),

    url(r'^families/(?P<family_slug>[^/]+)/$',
        Resource(handler=handlers.FamilyHandler), name='api-family'),

    url(r'^genera/(?P<genus_slug>[^/]+)/$',
        Resource(handler=handlers.GenusHandler), name='api-genus'),

    url(r'^$', 'nonexistent', name='api-base'),  # helps compute the base URL
    )

# We only use caching if memcached itself is configured; otherwise, we
# assume that the developer does not really intend caching to take
# place.

def c(view):
    if 'memcache' in settings.CACHES['default']['BACKEND']:
        one_hour = 60 * 60
        turn_on_browser_cache = cache_control(maxage=one_hour)
        turn_on_memcached = cache_page(one_hour)
        view = turn_on_browser_cache(view)
        view = turn_on_memcached(view)
        return view
    else:
        return view

urlpatterns += patterns(
    'gobotany.api.views',
    url(r'^glossaryblob/$', c(views.glossary_blob)),
    url(r'^species/([\w-]+)/$', c(views.species)),
    url(r'^vectors/character/([\w()-]+)/$', c(views.vectors_character)),
    url(r'^vectors/key/([\w-]+)/$', c(views.vectors_key)),
    url(r'^vectors/pile/([\w-]+)/$', c(views.vectors_pile)),
    )

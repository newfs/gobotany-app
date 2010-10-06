from django.conf.urls.defaults import patterns, url
from django.contrib import admin

from gobotany.api import handlers
from piston.resource import Resource

admin.autodiscover()

handler500 = 'django.views.defaults.server_error'

urlpatterns = patterns(
    '',

    url(r'^taxon/(?P<scientific_name>[^/]+)/$',
        Resource(handler=handlers.TaxonQueryHandler), name='api-taxon'),
    url(r'^taxon/$',
        Resource(handler=handlers.TaxonQueryHandler), name='api-taxon-list'),

    url(r'^taxon-count/$',
        Resource(handler=handlers.TaxonCountHandler), name='api-taxon-count'),
    # Suggested eventual replacement URL (plural) for taxon-count above
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
    url(r'^piles/(?P<slug>[^/]+)/?$',
        Resource(handler=handlers.PileHandler), name='api-pile'),

    url(r'^piles/(?P<pile_slug>[^/]+)/characters/$',
        Resource(handler=handlers.CharacterListingHandler), 
        name='api-character-list'),

    url(r'^piles/(?P<pile_slug>[^/]+)/(?P<character_short_name>[^/]+)/$',
        Resource(handler=handlers.CharacterValuesHandler), 
        name='api-character-values'),

    url(r'^pilegroups/$',
        Resource(handler=handlers.PileGroupListingHandler), 
        name='api-pilegroup-list'),
    url(r'^pilegroups/(?P<slug>[^/]+)/$',
        Resource(handler=handlers.PileGroupHandler), name='api-pilegroup'),

    url(r'^glossaryblob/$', Resource(handler=handlers.GlossaryBlobHandler)),
    )

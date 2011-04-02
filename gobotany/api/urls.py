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

    url(r'^maps/(?P<genus>[^/]+)-(?P<specific_epithet>[^/]+)-distribution-map(\.svg|/)?$',
        Resource(handler=handlers.DistributionMapHandler), name='distribution-map'),

    url(r'^families/(?P<family_slug>[^/]+)/$',
        Resource(handler=handlers.FamilyHandler), name='api-family'),
        
    url(r'^genera/(?P<genus_slug>[^/]+)/$',
        Resource(handler=handlers.GenusHandler), name='api-genus'),
        
    url(r'^plant-names/',
        Resource(handler=handlers.PlantNamesHandler), name='api-plant-names'),

    url(r'^$', 'nonexistent', name='api-base')
    )

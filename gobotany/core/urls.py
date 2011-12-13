from autocomplete.views import autocomplete

from gobotany.core import views
from gobotany.core import models

autocomplete.register(
    id='character_value',
    queryset=models.CharacterValue.objects.all(),
    fields=('character__short_name__istartswith', 'value_str__istartswith'),
    limit=100)
autocomplete.register(
    id='character',
    queryset=models.Character.objects.all(),
    fields=('short_name__istartswith',),
    limit=20)
autocomplete.register(
    id='taxon',
    queryset=models.Taxon.objects.all(),
    fields=('scientific_name__icontains',),
    limit=20)

urlpatterns = patterns(
    '',
    url('^$', views.default_view),

    url(r'^taxon-search/$', views.taxon_search),
    url(r'^canonical-images?$', views.canonical_images),
    url(r'^species-lists/$', views.species_lists),
    url(r'^best-characters/$', views.pile_characters_select),
    url(r'^best-characters/(?P<pile_slug>.*)/$', views.pile_characters),
    url(r'^piles-pile-groups$', views.piles_pile_groups),
    url('^autocomplete/(\w+)/$', autocomplete, name='autocomplete'),
    )

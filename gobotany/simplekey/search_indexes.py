from haystack import indexes
from haystack import site
from gobotany.core.models import Taxon


class TaxonIndex(indexes.SearchIndex):
    scientific_name = indexes.CharField(model_attr='scientific_name')
    text = indexes.CharField(
        document=True, use_template=True,
        template_name='simplekey/search_text_taxon.txt')

    def get_queryset(self):
        return Taxon.objects.filter(simple_key=True)


site.register(Taxon, TaxonIndex)

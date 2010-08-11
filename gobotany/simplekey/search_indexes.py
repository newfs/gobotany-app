from haystack import indexes
from haystack import site
from gobotany.core.models import Taxon


class TaxonIndex(indexes.SearchIndex):
    scientific_name = indexes.CharField(
        document=True, model_attr='scientific_name')


site.register(Taxon, TaxonIndex)

from gobotany import models


class SpeciesReader(object):

    def query_species(self,
                      scientific_name=None,
                      **kwargs):

        if scientific_name:
            return models.Taxon.objects.filter(scientific_name=scientific_name)
        else:
            base_query = models.Taxon.objects
            for k, v in kwargs.items():
                 base_query = base_query.filter(
                     character_values__character__short_name=k,
                     character_values__value=v)
            return base_query

_reader = SpeciesReader()
query_species = _reader.query_species

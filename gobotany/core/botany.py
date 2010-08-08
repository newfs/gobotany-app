from gobotany.core import models

CHAR_MAP = {
    u'TEXT': 'character_values__value_str',
    u'LENGTH': 'character_values__value_int',
    u'RATIO': 'character_values__value_flt',
    }


class SpeciesReader(object):

    def query_species(self,
                      scientific_name=None,
                      is_simple_key=True,
                      **kwargs):
        if scientific_name is not None:
            return models.Taxon.objects.filter(
                scientific_name__iexact=scientific_name,
                simple_key=is_simple_key)
        else:
            base_query = models.Taxon.objects
            for k, v in kwargs.items():
                if k == 'pilegroup':
                    base_query = base_query.filter(piles__pilegroup__slug=v)
                elif k == 'pile':
                    base_query = base_query.filter(piles__slug=v)
                elif k == 'family':
                    base_query = base_query.filter(family__name=v)
                elif k == 'genus':
                    base_query = base_query.filter(genus__name=v)
                else:
                    character = models.Character.objects.get(short_name=k)

                    if character.value_type == u'LENGTH':
                        base_query = base_query.filter(
                            character_values__character=character,
                            character_values__value_min__lte=v,
                            character_values__value_max__gte=v)

                    else: # assume type 'TEXT'
                        base_query = base_query.filter(
                            character_values__character=character,
                            character_values__value_str=v)


            return base_query.filter(simple_key=is_simple_key)

    def species_images(self, species, max_rank=10,
                       image_types=None):
        query = {'rank__lte': max_rank}
        if image_types:
            if isinstance(image_types, basestring):
                image_types = [s.strip() for s in image_types.split(',')]
            query['image_type__name__in'] = image_types
        # If we have a string assume it's the scientific name, otherwise
        # we have a taxon object or id
        if isinstance(species, basestring):
            species = models.Taxon.objects.get(scientific_name__iexact=species)
        return species.images.filter(**query)

_species_reader = SpeciesReader()
query_species = _species_reader.query_species
species_images = _species_reader.species_images

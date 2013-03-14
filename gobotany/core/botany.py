"""A Python API for complex operations designed for exposure through REST."""

from gobotany.core import models


CHAR_MAP = {
    u'TEXT': 'character_values__value_str',
    u'LENGTH': 'character_values__value_int',
    u'RATIO': 'character_values__value_flt',
    }


class SpeciesReader(object):

    def query_species(self, scientific_name=None, **kw):
        """Support rich queries for species stored as `Taxon` objects.

        This function supports both a primitive query for a single
        species, and also complex multi-field queries that can return
        zero or several matching species.  In either case, a Django
        query object is returned which the caller can further qualify
        with additional ``filter()`` calls, or invoke immediately with
        the ``all()`` method.

        To ask for a single species, provide its scientific name::

          objects = query_species(scientific_name='Isoetes echinospora')

        Running this query will yield a list of zero or one taxa.

        Queries for possibly many taxa can be built up by providing
        several keyword arguments; here are all of the different kinds
        of keywords that are supported::

          objects = query_species(
              pilegroup='ferns',
              pile='lycophytes',
              family='Isoetaceae',
              genus='Isoetes',
              <character_short_name>=<character_value>, ...
              )

        """
        if scientific_name is not None:
            return models.Taxon.objects.filter(
                scientific_name__iexact=scientific_name)
        else:
            base_query = models.Taxon.objects
            for k, v in kw.items():
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
                            character_values__value_min__lte=float(v),
                            character_values__value_max__gte=float(v),
                            )

                    else: # assume type 'TEXT'
                        base_query = base_query.filter(
                            character_values__character=character,
                            character_values__value_str=v)


            return base_query

    def species_images(self, species, max_rank=10, image_types=None):
        """Return a Django query for images of the given `species`.

        `species` - either a Taxon object, or a scientific name string.
        `max_rank` - return images with lower or equal rank than this.
        `image_types` - instead of returning images of all types, return
            only images whose type is in this list, which can be given
            as either a list of ImageType objects, or as a string of
            comma-separated image type names.

        """
        query = {'rank__lte': max_rank}
        if image_types:
            if isinstance(image_types, basestring):
                image_types = [s.strip() for s in image_types.split(',')]
            query['image_type__name__in'] = image_types
        # If we have a string assume it's the scientific name, otherwise
        # we have a taxon object or id
        if isinstance(species, basestring):
            species = models.Taxon.objects.get(scientific_name__iexact=species)

        species_images = None
        if species:
            species_images = species.images.filter(**query)

        return species_images

_species_reader = SpeciesReader()
query_species = _species_reader.query_species
species_images = _species_reader.species_images

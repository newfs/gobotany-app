"""Translate to and from flat CSV-friendly data."""


from gobotany.core import models


class PartnerPlants(object):
    """Which plants are displayed on a partner site.

    scientific_name,belongs_in_simple_key
    Abelmoschus esculentus,no
    Abies balsamea,yes
    Abies concolor,no
    ...

    """
    def __init__(self, partner):
        self.partner = partner

    def generate_records(self):
        plants = (models.PartnerSpecies.objects
                  .filter(partner=self.partner)
                  .select_related('species')
                  .order_by('species__scientific_name'))
        for plant in plants:
            flag = 'yes' if plant.simple_key else 'no'
            yield (plant.species.scientific_name, flag)

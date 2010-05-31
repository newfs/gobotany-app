from gobotany import models


class SpeciesReader(object):

    def query_species(self,
                      scientific_name=None,
                      **kwargs):

        res = []
        if scientific_name:
            for x in models.Taxon.objects.filter(
                scientific_name=scientific_name):
                res.append(x)
        else:
            for k, v in kwargs.items():
                chars = models.Character.objects.filter(short_name=k)
                for char in chars:
                    cvs = models.CharacterValue.objects.filter(value=v,
                                                               character=char)
                    for cv in cvs:
                        tcvs = models.TaxonToCharacterValue.objects.filter(
                            character_value=cv)
                        for tcv in tcvs:
                            res.append(tcv.taxon)

        return res

_reader = SpeciesReader()
query_species = _reader.query_species

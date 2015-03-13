from django.core.management.base import BaseCommand

from gobotany.core.models import Distribution

class Command(BaseCommand):
    help = ('Splits the scientific_name and populates the species_name and '
        'subspecific_epithet fields')

    def handle(self, *args, **options):
        for record in Distribution.objects.all():
            parts = record.scientific_name.split(' ')

            if 'x' in parts or 'X' in parts:
                # handle hybrids
                species_name = ' '.join(parts[0:3])
                subspecific_epithet = ' '.join(parts[3:])
            else:
                species_name = ' '.join(parts[0:2])
                subspecific_epithet = ' '.join(parts[2:])

            record.species_name = species_name
            record.subspecific_epithet = subspecific_epithet
            record.save()

            message = record.scientific_name + ' --> ' + record.species_name
            if record.subspecific_epithet:
                message += ' | ' + record.subspecific_epithet
            self.stdout.write(message)

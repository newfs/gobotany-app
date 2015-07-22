import random

from datetime import datetime, timedelta

from django.core.management.base import BaseCommand

from gobotany.plantshare.models import Location, Sighting, User

class Command(BaseCommand):
    """Create a set of dummy sightings for testing during development.

    The dummy sightings each have a randomly chosen plant name, location,
    and date within the current year. A first argument specifies the
    amount of sightings to be created. A second argument specifies the
    user name with which to associate the sightings.

    Example:

    dev/django create_dummy_sightings 10 bsmith
    """
    args = '<amount> <username>'
    help = ('Creates the specified amount of dummy sightings for the '
        'specified user name.')

    def _random_datetime(self, start, end):
        return start + timedelta(seconds=random.randint(0,
            int((end - start).total_seconds())))

    def _create_dummy_sighting(self, username):
        user = User.objects.get(username=username)
        year = datetime.now().year
        start = datetime(year, 1, 1, 00, 00)
        end = datetime(year, 12, 31, 23, 59)
        created = self._random_datetime(start, end)
        identification = 'Acer saccharum'
        location = Location(user_input='Boston, Ma.')
        location.latitude = 41.73 + random.uniform(-0.1, 0.1)
        location.longitude = 71.43 + random.uniform(-0.1, 0.1)
        location.save()
        self.stdout.write('_create_dummy_sighting: %s, %s, %s, %s' %
            (user, created, identification, location))
        sighting = Sighting(user=user, created=created,
            identification=identification, location=location)
        sighting.save()

    def handle(self, *args, **options):
        amount = int(args[0])
        username = args[1]
        for i in xrange(1, amount + 1):
            self.stdout.write('%d: %s' % (i, username))
            self._create_dummy_sighting(username)

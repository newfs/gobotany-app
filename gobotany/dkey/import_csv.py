"""Import CSV files related to the dichotomous key."""

from gobotany import settings
from django.core import management
management.setup_environ(settings)

import argparse
import csv
from django.db import connection, transaction
from gobotany.dkey import models

class Dummy():
    pass

def main():
    """Parse and act upon command-line arguments."""

    parser = argparse.ArgumentParser(description='Import a CSV file.')
    parser.add_argument(
        'csvpath', help='path to dkey_illustrative_species.csv')

    args = parser.parse_args()
    csvfile = Dummy()
    csvfile.open = lambda: open(args.csvpath)
    import_illustrative_species(csvfile)

@transaction.commit_on_success
def import_illustrative_species(csvfile):
    """Read a CSV file full of illustrative species."""

    records = list(csv.DictReader(csvfile.open()))

    cursor = connection.cursor()
    cursor.execute('DELETE FROM dkey_illustrativespecies')

    for record in records:
        i = models.IllustrativeSpecies()
        for key, value in record.items():
            setattr(i, key, value)
        i.save()

if __name__ == '__main__':
    main()

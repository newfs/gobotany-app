"""Import CSV files related to the dichotomous key."""

from gobotany import settings
from django.core import management
management.setup_environ(settings)

import argparse
import csv
from django.db import connection, transaction
from gobotany.dkey import models

def main():
    """Parse and act upon command-line arguments."""

    parser = argparse.ArgumentParser(description='Import a CSV file.')
    parser.add_argument(
        'csvpath', help='path to dkey_illustrative_species.csv')

    args = parser.parse_args()
    import_illustrative_species(args.csvpath)

@transaction.commit_on_success
def import_illustrative_species(csvpath):
    """Read a CSV file full of illustrative species."""

    with open(csvpath) as f:
        records = list(csv.DictReader(f))

    cursor = connection.cursor()
    cursor.execute('DELETE FROM dkey_illustrativespecies')

    for record in records:
        i = models.IllustrativeSpecies()
        for key, value in record.items():
            setattr(i, key, value)
        i.save()

if __name__ == '__main__':
    main()

from django.test import TestCase

from gobotany.mapping.map import NewEnglandPlantDistributionMap

class NewEnglandPlantDistributionMapTestCase(TestCase):
    def setUp(self):
        self.distribution_map = NewEnglandPlantDistributionMap()

    def test_map_init(self):
        self.assertTrue(self.distribution_map)

    def test_get_label_for_status_native(self):
        statuses = ['present', 'native', 'present|native']
        for status in statuses:
            self.assertEqual('native',
                self.distribution_map._get_label_for_status(status))

    def test_get_label_for_status_rare(self):
        statuses = ['rare', 'present|rare']
        for status in statuses:
            self.assertEqual('rare',
                self.distribution_map._get_label_for_status(status))

    def test_get_label_for_status_introduced(self):
        statuses = ['exotic', 'present|exotic']
        for status in statuses:
            self.assertEqual('introduced',
                self.distribution_map._get_label_for_status(status))

    def test_get_label_for_status_invasive(self):
        statuses = ['noxious', 'present|noxious']
        for status in statuses:
            self.assertEqual('invasive',
                self.distribution_map._get_label_for_status(status))

    def test_get_label_for_status_historic(self):
        statuses = ['extirpated', 'present|extirpated']
        for status in statuses:
            self.assertEqual('historic',
                self.distribution_map._get_label_for_status(status))

    def test_get_label_for_status_absent(self):
        statuses = ['absent', 'absent|eradicated']
        for status in statuses:
            self.assertEqual('absent',
                self.distribution_map._get_label_for_status(status))

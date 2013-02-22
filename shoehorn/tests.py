from unittest import TestCase
from .engine import DifferenceEngine

presidents = [['Washington'], ['Adams'], ['Jefferson']]

class Tests(TestCase):

    def test_empties(self):
        e = DifferenceEngine()
        e.differentiate([], [], [0])
        self.assertEqual(e.inserts, [])
        self.assertEqual(e.updates, [])
        self.assertEqual(e.deletes, [])

    def test_identicals(self):
        e = DifferenceEngine()
        e.differentiate(presidents, presidents, [0])
        self.assertEqual(e.inserts, [])
        self.assertEqual(e.updates, [])
        self.assertEqual(e.deletes, [])

    def test_insert_only(self):
        e = DifferenceEngine()
        e.differentiate([], presidents, [0])
        self.assertEqual(e.inserts, presidents)
        self.assertEqual(e.updates, [])
        self.assertEqual(e.deletes, [])

    def test_delete_only(self):
        e = DifferenceEngine()
        e.differentiate(presidents, [], [0])
        self.assertEqual(e.inserts, [])
        self.assertEqual(e.updates, [])
        self.assertEqual(e.deletes, presidents)

    def test_mixed(self):
        e = DifferenceEngine()
        seq1 = [['King George III']] + presidents
        seq2 = presidents[:2] + [['Madison']]
        e.differentiate(seq1, seq2, [0])
        self.assertEqual(e.inserts, [['Madison']])
        self.assertEqual(e.updates, [])
        self.assertEqual(e.deletes, [['King George III'], ['Jefferson']])

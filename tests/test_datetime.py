import os
import sys
import unittest
from typing import override

from sphinxnotes.data import Field

sys.path.insert(0, os.path.abspath('./src/sphinxnotes'))
from any.datetime import DATE_FMTS, PartialDate


class TestDatetime(unittest.TestCase):
    @override
    def setUp(self):
        DATE_FMTS.extend(['%Y-%m-%d', '%Y-%m', '%Y'])

    def test_datetime(self):
        val = Field.from_dsl('date').parse('2023-10-01')
        self.assertIsInstance(val, PartialDate)
        self.assertEqual(val, PartialDate(2023, 10, 1))

        # Missing day
        val = Field.from_dsl('date').parse('2023-10')
        self.assertIsInstance(val, PartialDate)
        self.assertEqual(val, PartialDate(2023, 10))

        # Missing month
        val = Field.from_dsl('date').parse('2023')
        self.assertIsInstance(val, PartialDate)
        self.assertEqual(val, PartialDate(2023))

    # ==========================
    # Errors
    # ==========================

    def test_unsupported_modifier(self):
        with self.assertRaisesRegex(ValueError, 'Unsupported type'):
            Field.from_dsl('list of unknown')

        with self.assertRaisesRegex(ValueError, 'Unknown modifier'):
            Field.from_dsl('int, random_mod')

    def test_invalid_formats(self):
        with self.assertRaisesRegex(ValueError, 'Failed to parse'):
            Field.from_dsl('date').parse('not-a-date')

        with self.assertRaisesRegex(ValueError, 'Failed to parse'):
            Field.from_dsl('date').parse('2023/13/45')


if __name__ == '__main__':
    unittest.main()

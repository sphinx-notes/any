import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath('./src/sphinxnotes'))
from any.domain import ObjDomain, PendingObject


class TestPendingObjectResolve(unittest.TestCase):
    def setUp(self):
        self.domain = ObjDomain(MagicMock())
        self.domain.data['objects'] = {}
        self.domain.data['references'] = {}

    def test_resolve_by_id(self):
        obj = MagicMock()
        self.domain.objects['foo', 'id1'] = ('doc1', 'anchor1', obj)

        pending = PendingObject(domain=self.domain, objtype='foo', objid='id1')
        result = pending.resolve()

        self.assertIs(result, obj)

    def test_resolve_by_reference(self):
        obj = MagicMock()
        self.domain.objects['foo', 'id1'] = ('doc1', 'anchor1', obj)
        self.domain.references['foo', 'field1', 'ref1'] = {'id1'}

        pending = PendingObject(domain=self.domain, objtype='foo', objid='ref1')
        result = pending.resolve()

        self.assertIs(result, obj)

    def test_resolve_not_found(self):
        self.domain.objects['foo', 'id1'] = ('doc1', 'anchor1', MagicMock())
        self.domain.references['foo', 'field1', 'ref1'] = {'id1'}

        pending = PendingObject(domain=self.domain, objtype='foo', objid='nonexistent')

        with self.assertRaises(KeyError):
            pending.resolve()

    def test_resolve_multiple_references(self):
        obj1 = MagicMock()
        obj2 = MagicMock()
        self.domain.objects['foo', 'id1'] = ('doc1', 'anchor1', obj1)
        self.domain.objects['foo', 'id2'] = ('doc2', 'anchor2', obj2)
        self.domain.references['foo', 'field1', 'ref1'] = {'id1', 'id2'}

        pending = PendingObject(domain=self.domain, objtype='foo', objid='ref1')
        result = pending.resolve()

        self.assertIn(result, [obj1, obj2])


if __name__ == '__main__':
    unittest.main()

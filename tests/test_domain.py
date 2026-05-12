import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath('./src/sphinxnotes'))
from any.domain import ObjDomain, PendingObject


class TestPendingObjectResolve(unittest.TestCase):
    def setUp(self):
        self.env = MagicMock()
        self.domain = ObjDomain(MagicMock())
        self.domain.name = 'obj'
        self.domain.data['objects'] = {}
        self.domain.data['references'] = {}
        self.env.get_domain.return_value = self.domain

    def test_resolve_by_id(self):
        obj = MagicMock()
        self.domain.objects['foo', 'id1'] = ('doc1', 'anchor1', obj)

        pending = PendingObject(domain_name='obj', objtype='foo', objid='id1')
        result = pending.resolve(self.env)

        self.assertIs(result, obj)

    def test_resolve_by_reference(self):
        obj = MagicMock()
        self.domain.objects['foo', 'id1'] = ('doc1', 'anchor1', obj)
        self.domain.references['foo', 'field1', 'ref1'] = {'id1'}

        pending = PendingObject(domain_name='obj', objtype='foo', objid='ref1')
        result = pending.resolve(self.env)

        self.assertIs(result, obj)

    def test_resolve_not_found(self):
        self.domain.objects['foo', 'id1'] = ('doc1', 'anchor1', MagicMock())
        self.domain.references['foo', 'field1', 'ref1'] = {'id1'}

        pending = PendingObject(domain_name='obj', objtype='foo', objid='nonexistent')

        with self.assertRaises(KeyError):
            pending.resolve(self.env)

    def test_resolve_multiple_references(self):
        obj1 = MagicMock()
        obj2 = MagicMock()
        self.domain.objects['foo', 'id1'] = ('doc1', 'anchor1', obj1)
        self.domain.objects['foo', 'id2'] = ('doc2', 'anchor2', obj2)
        self.domain.references['foo', 'field1', 'ref1'] = {'id1', 'id2'}

        pending = PendingObject(domain_name='obj', objtype='foo', objid='ref1')
        result = pending.resolve(self.env)

        self.assertIn(result, [obj1, obj2])


if __name__ == '__main__':
    unittest.main()

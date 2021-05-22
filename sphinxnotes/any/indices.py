"""
    sphinxnotes.any.indices
    ~~~~~~~~~~~~~~~~~~~~~~~

    Object index implementations

    :copyright: Copyright 2021 Shengyu Zhang
    :license: BSD, see LICENSE for details.
"""
from typing import Iterable, List, Tuple, Dict, Set, Optional, Type
from sphinx.domains import Index, IndexEntry

from .schema import Schema

class AnyIndex(Index):
    """
    Index subclass to provide the object reference index.
    """

    schema:Schema
    # TODO: document
    field:Optional[str] = None

    name:str
    localname:str
    shortname:str

    @classmethod
    def derive(cls, schema:Schema, field:str=None) -> Type["AnyIndex"]:
        """Generate an AnyIndex child class for indexing object."""
        dispfield = field or ''
        return type('Any%s%sIndex' % (schema.objtype.title(), dispfield.title()),
                    (cls,),
                    { 'schema': schema,
                     'field': field,
                     'name': '%s%sindex' % (schema.objtype, dispfield),
                     'localname': '%s %s Reference Index' % (
                         schema.objtype.title(), dispfield.title()),
                     'shortname': 'references',})


    def generate(self, docnames:Iterable[str] = None
                 ) -> Tuple[List[Tuple[str,List[IndexEntry]]], bool]:
        """Override parent method."""
        content = {}  # type: Dict[str, List[IndexEntry]]
        # List of all references
        objrefs = sorted(self.domain.data['references'].items())

        # Reference value -> object IDs
        objs_with_same_ref:Dict[str,Set[str]] = {}

        for (objtype, objfield, objref), objids in objrefs:
            if objtype != self.schema.objtype:
                continue
            if self.field and objfield != self.field:
                continue
            objs = objs_with_same_ref.setdefault(objref, set())
            objs.update(objids)

        for objref, objids in sorted(objs_with_same_ref.items()):
            # Add a entry for objref
            # 1: Entry with sub-entries.
            entries = content.setdefault(objref, [])
            for objid in sorted(objids):
                docname, anchor, obj = self.domain.data['objects'][self.schema.objtype, objid]
                if docnames and docname not in docnames:
                    continue
                idfield, _ = self.schema.identifier_of(obj)
                extra = f'{idfield}: {objid}' if idfield else ''
                name = self.schema.title_of(obj) or ''
                desc = self.schema.content_of(obj)[:50] + '…'
                # 0: Normal entry
                entries.append(IndexEntry(name, 0, docname, anchor, extra, '', desc))

        # sort by first letter
        sorted_content = sorted(content.items())

        return sorted_content, False

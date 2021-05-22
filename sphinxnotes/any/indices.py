"""
    sphinxnotes.any.indices
    ~~~~~~~~~~~~~~~~~~~~~~~

    Object index implementations

    :copyright: Copyright 2021 Shengyu Zhang
    :license: BSD, see LICENSE for details.
"""
from typing import Iterable, List, Tuple, Dict
from sphinx.domains import Index, IndexEntry

from .schema import Schema

class AnyIndex(Index):
    """
    Index subclass to provide the object reference index.
    """

    schema:Schema

    name:str
    localname:str
    shortname:str

    def generate(self, docnames:Iterable[str] = None
                 ) -> Tuple[List[Tuple[str,List[IndexEntry]]], bool]:
        """Override parent method."""

        content = {}  # type: Dict[str, List[IndexEntry]]
        # list of all modules, sorted by module name
        objrefs = sorted(self.domain.data['references'].items())
        for (objtype, objfield, objref), objids in objrefs:
            if objtype != self.schema.objtype:
                continue

            entries = content.setdefault(objref, [])

            for objid in objids:
                docname, anchor, obj = self.domain.data['objects'][objtype, objid]
                if docnames and docname not in docnames:
                    continue
                entries.append(IndexEntry(objref, 0, docname, anchor, '', '', ''))

        # sort by first letter
        sorted_content = sorted(content.items())

        return sorted_content, False

"""
sphinxnotes.any.indices
~~~~~~~~~~~~~~~~~~~~~~~

Object index implementations

:copyright: Copyright 2021 Shengyu Zhang
:license: BSD, see LICENSE for details.
"""

from typing import Iterable, TypeVar
import re

from sphinx.domains import Domain, Index, IndexEntry
from sphinx.util import logging
from docutils import core, nodes
from docutils.parsers.rst import roles

from .schema import Schema, Value, Classifier, Classif

logger = logging.getLogger(__name__)


class AnyIndex(Index):
    """
    Index subclass to provide the object reference index.
    """

    domain: Domain  # for type hint
    schema: Schema
    field: str | None = None
    classifier: Classifier

    @classmethod
    def derive(
        cls, schema: Schema, field: str | None, classifier: Classifier
    ) -> type['AnyIndex']:
        """Generate an AnyIndex child class for indexing object."""
        # TODO: add Indexer.name
        if field:
            typ = f'Any{schema.objtype.title()}{field.title()}Index'
            name = schema.objtype + '.' + field  # TOOD: objtype_and_objfield_to_reftype
            localname = f'{schema.objtype.title()} {field.title()} Reference Index'
        else:
            typ = f'Any{schema.objtype.title()}Index'
            name = schema.objtype
            localname = f'{schema.objtype.title()} Reference Index'
        return type(
            typ,
            (cls,),
            {
                'name': name,
                'localname': localname,
                'shortname': 'references',
                'schema': schema,
                'field': field,
                'classifier': classifier,
            },
        )

    def generate(
        self, docnames: Iterable[str] | None = None
    ) -> tuple[list[tuple[str, list[IndexEntry]]], bool]:
        """Override parent method."""

        # Single index for generating normal entries (subtype=0).
        # Category (lv1) →  Category (for ordering objids) →  objids
        singleidx: dict[Classif, dict[Classif, set[str]]] = {}
        # Dual index for generating entrie (subtype=1) and its sub-entries (subtype=2).
        # Category (lv1) →  Category (lv2) →  Category (for ordering objids) →  objids
        dualidx: dict[Classif, dict[Classif, dict[Classif, set[str]]]] = {}

        objrefs = sorted(self.domain.data['references'].items())
        for (objtype, objfield, objref), objids in objrefs:
            if objtype != self.schema.objtype:
                continue
            if self.field and objfield != self.field:
                continue

            # TODO: pass a real value
            for catelog in self.classifier.classify(Value(objref)):
                category = catelog.as_category()
                entry = catelog.as_entry()
                if entry is None:
                    singleidx.setdefault(category, {}).setdefault(
                        catelog, set()
                    ).update(objids)
                else:
                    dualidx.setdefault(category, {}).setdefault(entry, {}).setdefault(
                        catelog, set()
                    ).update(objids)

        content: dict[Classif, list[IndexEntry]] = {}  # category →  entries
        for category, entries in self._sort_by_catelog(singleidx):
            index_entries = content.setdefault(category, [])
            for category, objids in self._sort_by_catelog(entries):
                for objid in objids:
                    entry = self._generate_index_entry(objid, docnames, category)
                    if entry is None:
                        continue
                    index_entries.append(entry)

        for category, entries in self._sort_by_catelog(dualidx):
            index_entries = content.setdefault(category, [])
            for entry, subentries in self._sort_by_catelog(entries):
                index_entries.append(self._generate_empty_index_entry(entry))
                for subentry, objids in self._sort_by_catelog(subentries):
                    for objid in objids:
                        entry = self._generate_index_entry(objid, docnames, subentry)
                        if entry is None:
                            continue
                        index_entries.append(entry)

        # sort by category, and map classif -> str
        sorted_content = [
            (classif.leaf, entries)
            for classif, entries in self._sort_by_catelog(content)
        ]

        return sorted_content, False

    def _generate_index_entry(
        self, objid: str, ignore_docnames: Iterable[str] | None, category: Classif
    ) -> IndexEntry | None:
        docname, anchor, obj = self.domain.data['objects'][self.schema.objtype, objid]
        if ignore_docnames and docname not in ignore_docnames:
            return None
        name = self.schema.title_of(obj) or objid
        subtype = category.index_entry_subtype
        extra = category.leaf
        objcont = self.schema.content_of(obj)
        if isinstance(objcont, str):
            desc = objcont
        elif isinstance(objcont, list):
            desc = '\n'.join(objcont)  # FIXME: use schema.Form
        else:
            desc = ''
        desc = strip_rst_markups(desc)  # strip rst markups
        desc = ''.join([ln for ln in desc.split('\n') if ln.strip()])  # strip NEWLINE
        desc = desc[:50] + '…' if len(desc) > 50 else desc  # shorten
        return IndexEntry(
            name,  # the name of the index entry to be displayed
            subtype,  # the sub-entry related type
            docname,  # docname where the entry is located
            anchor,  # anchor for the entry within docname
            extra,  # extra info for the entry
            '',  # qualifier for the description
            desc,  # description for the entry
        )

    def _generate_empty_index_entry(self, category: Classif) -> IndexEntry:
        return IndexEntry(
            category.leaf, category.index_entry_subtype, '', '', '', '', ''
        )

    _T = TypeVar('_T')

    def _sort_by_catelog(self, d: dict[Classif, _T]) -> list[tuple[Classif, _T]]:
        """Helper for sorting dict items by Category."""
        return self.classifier.sort(d.items(), lambda x: x[0])


def strip_rst_markups(rst: str) -> str:
    """Strip markups and newlines in rST.

    .. warning: To make parsing success and no any side effects, we created a
    standalone rst praser, without any sphinx stuffs. Some many role functions
    registered by Sphinx (and Sphinx extension) will failed, so we remove all
    local (non-docutls builtin) role functions away from registry.
    While parsing role, these role functions will not be called because parser
    doesn't know it, and parser will generates nodes.problematic for unknown role.

    ..warning:: This function is not parallel-safe."""

    # Save and erase local roles.
    #
    # FIXME: sphinx.util.docutils.docutils_namespace() is a good utils to erase
    # and recover roles, but it panics Sphinx.
    # https://github.com/sphinx-doc/sphinx/issues/8978
    #
    # TODO: deal with directive.
    _roles, roles._roles = roles._roles, {}  # type: ignore[attr-defined]
    try:
        # https://docutils.sourceforge.io/docs/user/config.html
        settings = {
            'report_level': 4,  #  suppress error log
        }
        doctree = core.publish_doctree(rst, settings_overrides=settings)
        for n in doctree.findall(nodes.system_message):
            # Replace all system_message nodes.
            nop = nodes.literal('', ids=n.get('ids'))
            n.replace_self(nop)
        for n in doctree.findall(nodes.problematic):
            # Replace all problematic nodes and strip the role markups.
            if isinstance(n[0], nodes.Text):
                # :role:`text` →  text
                match = re.search(r'`([^`]+)`', n[0])
                if not match:
                    continue
                result = match.group(1)
                n.replace(n[0], nodes.Text(result))
        txt = doctree.astext()
    except Exception as e:
        logger.warning(f'failed to run publish_doctree: {e}')
        txt = rst
    finally:
        # Recover local roles.
        roles._roles = _roles  # type: ignore[attr-defined]

    return txt

"""
sphinxnotes.any.indices
~~~~~~~~~~~~~~~~~~~~~~~

Object index implementations

:copyright: Copyright 2021 Shengyu Zhang
:license: BSD, see LICENSE for details.
"""

from typing import Iterable, TypeVar
import re

from docutils import core, nodes
from docutils.parsers.rst import roles
from sphinx.domains import Domain, Index, IndexEntry
from sphinx.util import logging

from .objects import Schema, Value, Indexer, Category, RefType

logger = logging.getLogger(__name__)


class AnyIndex(Index):
    """
    Index subclass to provide the object reference index.
    """

    domain: Domain  # for type hint
    schema: Schema
    reftype: RefType
    indexer: Indexer

    @classmethod
    def derive(
        cls, schema: Schema, reftype: RefType, indexer: Indexer
    ) -> type['AnyIndex']:
        """Generate an AnyIndex child class for indexing object."""
        if reftype.field:
            clsname = f'Any{reftype.objtype.title()}{reftype.field.title()}Index'
            localname = (
                f'{reftype.objtype.title()} {reftype.field.title()} Reference Index'
            )
        else:
            clsname = f'Any{reftype.objtype.title()}Index'
            localname = f'{reftype.objtype.title()} Reference Index'
        if reftype.indexer:
            clsname += 'By' + reftype.indexer.title()
            localname += ' by ' + reftype.indexer.title()
        return type(
            clsname,
            (cls,),
            {
                # HTML builder will generate /<domain>-<name>.html index page.
                'name': str(reftype),
                'localname': localname,
                'shortname': 'references',
                'schema': schema,
                'reftype': reftype,
                'indexer': indexer,
            },
        )

    def generate(
        self, docnames: Iterable[str] | None = None
    ) -> tuple[list[tuple[str, list[IndexEntry]]], bool]:
        """Override parent method."""

        # Single index for generating normal entries (subtype=0).
        # Main Category →  Extra (for ordering objids) →  objids
        singleidx: dict[Category, dict[Category, set[str]]] = {}
        # Dual index for generating entrie (subtype=1) and its sub-entries (subtype=2).
        # Main category  →  Sub-Category →  Extra (for ordering objids) →  objids
        dualidx: dict[Category, dict[Category, dict[Category, set[str]]]] = {}

        objrefs = sorted(self.domain.data['references'].items())
        for (objtype, objfield, objref), objids in objrefs:
            if objtype != self.reftype.objtype:
                continue
            if self.reftype.field and objfield != self.reftype.field:
                continue

            # TODO: pass a real Value
            for category in self.indexer.classify(Value(objref)):
                main = category.as_main()
                sub = category.as_sub()
                if sub is None:
                    singleidx.setdefault(main, {}).setdefault(category, set()).update(
                        objids
                    )
                else:
                    dualidx.setdefault(main, {}).setdefault(sub, {}).setdefault(
                        category, set()
                    ).update(objids)

        content: dict[Category, list[IndexEntry]] = {}  # category →  entries
        for main, entries in self._sort_by_category(singleidx):
            index_entries = content.setdefault(main, [])
            for main, objids in self._sort_by_category(entries):
                for objid in objids:
                    entry = self._generate_index_entry(objid, docnames, main)
                    if entry is None:
                        continue
                    index_entries.append(entry)

        for main, entries in self._sort_by_category(dualidx):
            index_entries = content.setdefault(main, [])
            for sub, subentries in self._sort_by_category(entries):
                index_entries.append(self._generate_subcategory_index_entry(sub))
                for subentry, objids in self._sort_by_category(subentries):
                    for objid in objids:
                        entry = self._generate_index_entry(objid, docnames, subentry)
                        if entry is None:
                            continue
                        index_entries.append(entry)

        # sort by category, and map category -> str
        sorted_content = [
            (category.main, entries)
            for category, entries in self._sort_by_category(content)
        ]

        return sorted_content, False

    def _generate_index_entry(
        self, objid: str, ignore_docnames: Iterable[str] | None, category: Category
    ) -> IndexEntry | None:
        docname, anchor, obj = self.domain.data['objects'][self.reftype.objtype, objid]
        if ignore_docnames and docname not in ignore_docnames:
            return None
        name = self.schema.title_of(obj) or objid
        subtype = category.index_entry_subtype()
        extra = category.extra or ''
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

    def _generate_subcategory_index_entry(self, category: Category) -> IndexEntry:
        assert category.sub is not None
        return IndexEntry(
            category.sub, category.index_entry_subtype(), '', '', '', '', ''
        )

    _T = TypeVar('_T')

    def _sort_by_category(self, d: dict[Category, _T]) -> list[tuple[Category, _T]]:
        """Helper for sorting dict items by classif."""
        return self.indexer.sort(d.items(), lambda x: x[0])


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

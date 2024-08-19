"""
sphinxnotes.any.indices
~~~~~~~~~~~~~~~~~~~~~~~

Object index implementations

:copyright: Copyright 2021 Shengyu Zhang
:license: BSD, see LICENSE for details.
"""

from typing import Iterable
import re

from sphinx.domains import Index, IndexEntry
from sphinx.util import logging
from docutils import core, nodes
from docutils.parsers.rst import roles

from .schema import Schema

logger = logging.getLogger(__name__)


class AnyIndex(Index):
    """
    Index subclass to provide the object reference index.
    """

    schema: Schema
    # TODO: document
    field: str | None = None

    name: str
    localname: str
    shortname: str

    @classmethod
    def derive(cls, schema: Schema, field: str | None = None) -> type['AnyIndex']:
        """Generate an AnyIndex child class for indexing object."""
        if field:
            typ = f'Any{schema.objtype.title()}{field.title()}Index'
            name = schema.objtype + '.' + field
            localname = f'{schema.objtype.title()} {field.title()} Reference Index'
        else:
            typ = f'Any{schema.objtype.title()}Index'
            name = schema.objtype
            localname = f'{schema.objtype.title()} Reference Index'
        return type(
            typ,
            (cls,),
            {
                'schema': schema,
                'field': field,
                'name': name,
                'localname': localname,
                'shortname': 'references',
            },
        )

    def generate(
        self, docnames: Iterable[str] | None = None
    ) -> tuple[list[tuple[str, list[IndexEntry]]], bool]:
        """Override parent method."""
        content = {}  # type: dict[str, list[IndexEntry]]
        # list of all references
        objrefs = sorted(self.domain.data['references'].items())

        # Reference value -> object IDs
        objs_with_same_ref: dict[str, set[str]] = {}

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
                docname, anchor, obj = self.domain.data['objects'][
                    self.schema.objtype, objid
                ]
                if docnames and docname not in docnames:
                    continue
                name = self.schema.title_of(obj) or objid
                extra = '' if name == objid else objid
                objcont = self.schema.content_of(obj)
                if isinstance(objcont, str):
                    desc = objcont
                elif isinstance(objcont, list):
                    desc = '\n'.join(objcont)
                else:
                    desc = ''
                desc = strip_rst_markups(desc)  # strip rst markups
                desc = ''.join(
                    [ln for ln in desc.split('\n') if ln.strip()]
                )  # strip NEWLINE
                desc = desc[:50] + '…' if len(desc) > 50 else desc  # shorten
                # 0: Normal entry
                entries.append(IndexEntry(name, 0, docname, anchor, extra, '', desc))

        # sort by first letter
        sorted_content = sorted(content.items())

        return sorted_content, False


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

"""
sphinxnotes.obj.domain
~~~~~~~~~~~~~~~~~~~~~~

Domain implementions.

:copyright: Copyright 2021 Shengyu Zhang
:license: BSD, see LICENSE for details.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, override, cast, TypeVar

from docutils import nodes
from sphinx.addnodes import pending_xref
from sphinx.domains import Domain, ObjType, Index, IndexEntry
from sphinx.roles import XRefRole
from sphinx.util import logging
from sphinx.util.nodes import make_id, make_refnode
from sphinx.errors import ExtensionError

from sphinxnotes.data import (
    ValueWrapper,
    Schema,
    pending_node,
    RenderedNode,
    StrictDataDefineDirective,
)

from .obj import (
    Object,
    RefType,
    Templates,
    Category,
    Indexer,
    IndexerRegistry,
    get_object_uniq_ids,
    get_object_refs,
)

from .utils import strip_rst_markups

if TYPE_CHECKING:
    from typing import Iterator, Iterable, override
    from sphinx.builders import Builder
    from sphinx.environment import BuildEnvironment

logger = logging.getLogger(__name__)

# ===================
# Domain implemention
# ===================


class ObjDomain(Domain):
    """
    The Obj domain for describing anything.
    """

    """Parent's class members."""

    name = 'obj'
    label = 'Object'
    object_types = {}
    directives = {}
    roles = {}
    indices = []
    initial_data = {
        'objects': {},  # see property object
        'references': {},  # see property references
    }

    """Custom class members."""

    #: ObjDomain specific: reftype -> index class
    _indices_for_reftype: dict[str, type[ObjIndex]] = {}
    #: ObjDomain specific: objtype -> data schema
    _schemas: dict[str, Schema] = {}
    #: ObjDomain specific: objtype -> template set
    _templates: dict[str, Templates] = {}

    """Methods that override from parent."""

    @override
    def clear_doc(self, docname: str) -> None:
        objids = set()
        for (objtype, objid), (doc, _, _) in list(self.objects.items()):
            if doc == docname:
                del self.objects[objtype, objid]
                objids.add(objid)
        for (objtype, objfield, objref), ids in list(self.references.items()):
            ids = ids - objids
            if ids:
                self.references[objtype, objfield, objref] = ids
            else:
                del self.references[objtype, objfield, objref]

    @override
    def resolve_xref(
        self,
        env: BuildEnvironment,
        fromdocname: str,
        builder: Builder,
        typ: str,
        target: str,
        node: pending_xref,
        contnode: nodes.Element,
    ) -> nodes.reference | None:
        logger.debug('[any] resolveing xref of %s', (typ, target))

        reftype = RefType.parse(typ)
        objtype, objfield, objidx = reftype.objtype, reftype.field, reftype.indexer
        objids = set()
        if objidx:
            pass  # no need to lookup objds
        elif objfield:
            # NOTE: To prevent change domain data, dont use ``objids = xxx``
            if ids := self.references.get((objtype, objfield, target)):
                objids.update(ids)
        else:
            for (t, _, r), ids in self.references.items():
                if t == objtype and r == target:
                    objids.update(ids)

        extra_ctxs = {
            '_ref': {
                'title': contnode[0].astext(),
                'has_explicit_title': node['refexplicit'],
                'type': typ,
                'target': target,
            },
            '_objs': [],
        }

        if len(objids) > 1 or objidx is not None:
            # Mulitple objects found or reference index explicitly,
            # create link to indices page.
            todocname, anchor = self._get_index_anchor(typ, target)
            logger.debug(
                f'ambiguous {objtype} {target} in {self}, '
                + f'ids: {objids} index: {todocname}#{anchor}'
            )
        elif len(objids) == 1:
            todocname, anchor, obj = self.objects[objtype, objids.pop()]
            pending = pending_node()
            pending.inline = True
            pending.schema = self._schemas[objtype]
            pending.template = self._templates[objtype].ref
            contnode = pending
        else:
            # The pending_xref node may be resolved by intersphinx,
            # so do not emit warning here, see also warn_missing_reference.
            # FIXME
            return None

        refnode = make_refnode(
            builder, fromdocname, todocname, anchor, contnode, objtype + ' ' + target
        )
        refnode['classes'] += [self.name, self.name + '-' + objtype]
        return refnode

    @override
    def get_objects(self) -> Iterator[tuple[str, str, str, str, str, int]]:
        for (objtype, objid), (docname, anchor, _) in self.data['objects'].items():
            yield objid, objid, objtype, docname, anchor, 1

    """Publish methods."""

    @classmethod
    def add_object_type(cls, objtype: str, schema: Schema, tmpls: Templates) -> None:
        cls._schemas[objtype] = schema
        cls._templates[objtype] = tmpls

        # Create a directive for defining object.
        cls.directives[objtype] = ObjDefineDirective.derive(objtype, schema, tmpls.obj)

        def mkrole(reftype: RefType):
            """Create and register role for referencing object."""
            role = XRefRole(
                # Emit warning when missing reference (node['refwarn'] = True)
                warn_dangling=True,
            )
            cls.roles[str(reftype)] = role
            logger.debug(f'[any] make role {reftype} → {type(role)}')

        def mkindex(reftype: RefType):
            """Create and register object index."""
            assert reftype.indexer
            if not (indexer := IndexerRegistry.get(reftype.indexer)):
                raise ExtensionError(f'no such indexer "{reftype.indexer}"')
            index = ObjIndex.derive(reftype, indexer)
            cls.indices.append(index)
            cls._indices_for_reftype[str(reftype)] = index
            logger.debug(f'[any] make index {reftype} → {type(index)}')

        # Create all-in-one role and index (do not distinguish reference fields).
        reftypes = [RefType(objtype)]
        mkrole(reftypes[0])

        # Create {field,indexer}-specificed role and index.
        for name, field in schema.fields():
            if field.ref:
                reftype = RefType(objtype, name)
                reftypes.append(reftype)
                mkrole(reftype)  # create a role to reference object(s)

            for idxname in field.index:
                reftype = RefType(objtype, field=name, indexer=idxname)
                reftypes.append(reftype)
                # Create role and index for reference objects by index.
                mkrole(reftype)
                mkindex(reftype)

        cls.object_types[objtype] = ObjType(objtype, *[str(x) for x in reftypes])

    @property
    def objects(self) -> dict[tuple[str, str], tuple[str, str, Object]]:
        """(objtype, objid) -> (docname, anchor, obj)"""
        return self.data.setdefault('objects', {})

    @property
    def references(self) -> dict[tuple[str, str, str], set[str]]:
        """(objtype, objfield, objref) -> set(objid)"""
        return self.data.setdefault('references', {})

    def note_object(
        self, docname: str, anchor: str, schema: Schema, obj: Object
    ) -> None:
        objtype = next((k for k, v in self._schemas.items() if v == schema))

        objid = get_object_uniq_ids(schema, obj)[0]
        objrefs = get_object_refs(schema, obj)
        if (objtype, objid) in self.objects:
            other_docname, other_anchor, other_obj = self.objects[objtype, objid]
            logger.warning(
                f'duplicate identifier of {obj} at {docname}#{anchor}'
                + f'other object is {other_obj} at {other_docname}#{other_anchor}'
            )
        logger.debug(
            f'[any] note object {objtype} {objid} at {docname}#{anchor}, references: {objrefs}'
        )
        self.objects[objtype, objid] = (docname, anchor, obj)
        for objfield, objref in objrefs:
            self.references.setdefault((objtype, objfield, objref), set()).add(objid)

    """Methods for inernal use"""

    def _get_index_anchor(self, reftype: str, refval: str) -> tuple[str, str]:
        """
        Return the docname and anchor name of index page. Can be used for ``make_refnode()``.

        .. warning:: This is no public API of sphinx and may broken in future version.
        """
        domain = self.name
        index = self._indices_for_reftype[reftype]
        return f'{domain}-{index.name}', index.indexer.anchor(refval)


# =============================
# Directive/Roles implementions
# =============================


class ObjDefineDirective(StrictDataDefineDirective):
    schema: Schema

    @override
    def process_rendered_node(self, n: RenderedNode) -> None:
        domainname, objtype = self.name.split(':', 1)
        _domain = self.env.get_domain(domainname)
        domain = cast(ObjDomain, _domain)

        # Attach domain related info to section node
        n['domain'] = domain.name
        # 'desctype' is a backwards compatible attribute
        n['objtype'] = n['desctype'] = objtype
        n['classes'].append(domain.name)

        # FIXME: get anchor node
        if n.external_name is not None:
            objids = get_object_uniq_ids(self.schema, n.data)
            ahrid = make_id(
                self.env, self.state.document, prefix=objtype, term=objids[0]
            )

            n['ids'].append(ahrid)
            # Add object name to node's names attribute.
            # 'names' is space-separated list containing normalized reference
            # names of an element.
            n['names'].extend([nodes.fully_normalize_name(x) for x in objids])

            self.state.document.note_explicit_target(n)
            domain.note_object(self.env.docname, ahrid, self.schema, n.data)


# =================
# Index implemention
# ==================
#
# NOTE: There are cross-references between ObjIndex and ObjDomain,
# so they can only be implemented in the same Python file.


class ObjIndex(Index):
    """Index subclass to provide the object reference index."""

    reftype: RefType
    indexer: Indexer

    if TYPE_CHECKING:
        domain: ObjDomain

    @classmethod
    def derive(cls, reftype: RefType, indexer: Indexer) -> type[ObjIndex]:
        """Generate an ObjIndex child class for indexing object."""
        if reftype.field:
            clsname = f'Obj{reftype.objtype.title()}{reftype.field.title()}Index'
            localname = (
                f'{reftype.objtype.title()} {reftype.field.title()} Reference Index'
            )
        else:
            clsname = f'Obj{reftype.objtype.title()}Index'
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
                'reftype': reftype,
                'indexer': indexer,
            },
        )

    @override
    def generate(
        self, docnames: Iterable[str] | None = None
    ) -> tuple[list[tuple[str, list[IndexEntry]]], bool]:
        # Single index for generating normal entries (subtype=0).
        # Main Category →  Extra (for ordering objids) →  objids
        singleidx: dict[Category, dict[Category, set[str]]] = {}
        # Dual index for generating entrie (subtype=1) and its sub-entries (subtype=2).
        # Main category  →  Sub-Category →  Extra (for ordering objids) →  objids
        dualidx: dict[Category, dict[Category, dict[Category, set[str]]]] = {}

        objrefs = sorted(self.domain.references.items())
        for (objtype, objfield, objref), objids in objrefs:
            if objtype != self.reftype.objtype:
                continue
            if self.reftype.field and objfield != self.reftype.field:
                continue

            # TODO: pass a real Value
            for category in self.indexer.classify(objref):
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
        docname, anchor, obj = self.domain.objects[self.reftype.objtype, objid]
        if ignore_docnames and docname not in ignore_docnames:
            return None
        name = obj.title() or objid
        subtype = category.index_entry_subtype()
        extra = category.extra or ''
        desc = '.\n'.join(ValueWrapper(obj.content).as_str_list())
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

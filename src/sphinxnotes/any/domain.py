"""
sphinxnotes.obj.domain
~~~~~~~~~~~~~~~~~~~~~~

Domain implementions.

:copyright: Copyright 2021 Shengyu Zhang
:license: BSD, see LICENSE for details.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, override, cast, TypeVar
from pprint import pformat

from .indexers import LiteralIndexer, PathIndexer, YearIndexer, MonthIndexer

from docutils import nodes
from sphinx import addnodes
from sphinx.domains import Domain, ObjType, Index, IndexEntry
from sphinx.roles import XRefRole
from sphinx.util import logging
from sphinx.util.nodes import make_id, make_refnode
from sphinx.errors import ExtensionError
from sphinxnotes.data import (
    PlainValue,
    ValueWrapper,
    ParsedData,
    Schema,
    pending_node,
    rendered_node,
    StrictDataDefineDirective,
)
from sphinxnotes.data.utils import Report, find_nearest_block_element, find_parent

from .obj import (
    Object,
    RefType,
    Templates,
    Category,
    Indexer,
    get_object_title,
    get_object_uniq_ids,
    get_object_refs,
)
from .utils import strip_rst_markups

if TYPE_CHECKING:
    from typing import Iterator, Iterable
    from sphinx.builders import Builder
    from sphinx.environment import BuildEnvironment

logger = logging.getLogger(__name__)

# ===================
# Domain implemention
# ===================


class ObjDomain(Domain):
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
    indices_for_reftype: dict[str, type[ObjIndex]] = {}
    #: ObjDomain specific: objtype -> data schema
    schemas: dict[str, Schema] = {}
    #: ObjDomain specific: objtype -> template set
    templates: dict[str, Templates] = {}

    """Methods that override from parent."""

    @override
    def clear_doc(self, docname: str) -> None:
        objkeys = []
        for (objtype, objid), (doc, _, _) in self.objects.items():
            if doc == docname:
                objkeys.append((objtype, objid))

        objids = set()
        for objtype, objid in objkeys:
            del self.objects[objtype, objid]
            objids.add(objid)

        refkeys = []
        for (objtype, objfield, objref), ids in self.references.items():
            if ids := ids - objids:
                self.references[objtype, objfield, objref] = ids
            else:
                refkeys.append((objtype, objfield, objref))

        for objtype, objfield, objref in refkeys:
            del self.references[objtype, objfield, objref]

    @override
    def resolve_xref(
        self,
        env: BuildEnvironment,
        fromdocname: str,
        builder: Builder,
        typ: str,
        target: str,
        node: addnodes.pending_xref,
        contnode: nodes.Element,
    ) -> nodes.reference | None:
        logger.debug('[any] resolveing xref of %s', (typ, target))

        reftype = RefType.parse(typ)
        objtype, objfield, objidx = reftype.objtype, reftype.field, reftype.indexer
        objids = set()
        if objidx:
            pass  # no need to lookup objds
        elif objfield:
            # NOTE: Do not change domain data
            if ids := self.references.get((objtype, objfield, target)):
                objids.update(ids)
        else:
            for (t, _, r), ids in self.references.items():
                if t == objtype and r == target:
                    objids.update(ids)

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
            contnode = pending_node(
                obj, self.templates[objtype].get_ref_by(reftype), inline=True
            )
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
    def add_objtype(cls, objtype: str, schema: Schema, tmpls: Templates) -> None:
        cls.schemas[objtype] = schema
        cls.templates[objtype] = tmpls

        # Create a directive for defining object.
        cls.directives[objtype] = ObjDefineDirective.derive(
            objtype, schema, tmpls.content
        )

        def mkrole(reftype: RefType):
            """Create and register role for referencing object."""
            role = XRefRole(
                # Emit warning when missing reference (node['refwarn'] = True)
                warn_dangling=True,
            )
            cls.roles[str(reftype)] = role
            logger.debug(f'[any] make role {reftype} → {type(role)}')

        def mkindex(reftype: RefType, indexer: Indexer):
            """Create and register object index."""
            index = ObjIndex.derive(reftype, indexer)
            cls.indices.append(index)
            cls.indices_for_reftype[str(reftype)] = index
            logger.debug(f'[any] make index {reftype} → {type(index)}')

        # Create all-in-one role and index (do not distinguish reference fields).
        reftypes = [RefType(objtype)]
        if schema.name and schema.name.ref:
            mkrole(reftypes[0])
            if schema.name.uniq:
                mkindex(reftypes[0], DEFAULT_INDEXER)

        # Create {field,indexer}-specificed role and index.
        for name, field in schema.fields():
            if field.ref:
                reftype = RefType(objtype, name)
                reftypes.append(reftype)
                mkrole(reftype)  # create a role to reference object(s)
                if not field.uniq:
                    mkindex(reftype, DEFAULT_INDEXER)

            for idxname in field.index:
                reftype = RefType(objtype, field=name, indexer=idxname)
                reftypes.append(reftype)
                # Create role and index for reference objects by index.
                mkrole(reftype)
                if indexer := INDEXER_REGSITRY.get(idxname):
                    mkindex(reftype, indexer)
                else:
                    raise ExtensionError(f'no such indexer "{reftype.indexer}"')

        cls.object_types[objtype] = ObjType(objtype, *[str(x) for x in reftypes])

    @property
    def objects(self) -> dict[tuple[str, PlainValue], tuple[str, str, Object]]:
        """(objtype, objid) -> (docname, anchor, obj)"""
        return self.data.setdefault('objects', {})

    @property
    def references(self) -> dict[tuple[str, str, PlainValue], set[PlainValue]]:
        """(objtype, objfield, objref) -> set(objid)"""
        return self.data.setdefault('references', {})

    def note_object(
        self, docname: str, anchor: str, objtype: str, obj: Object
    ) -> tuple[str, str, Object] | None:
        schema = self.schemas[objtype]

        objid = get_object_uniq_ids(schema, obj)[0]
        objrefs = get_object_refs(schema, obj)

        logger.debug(
            f'[any] note object {objtype} {objid} at {docname}#{anchor}, references: {objrefs}'
        )

        otherobj = self.objects.get((objtype, objid))
        self.objects[objtype, objid] = (docname, anchor, obj)

        for objfield, objref in objrefs:
            self.references.setdefault((objtype, objfield, objref), set()).add(objid)

        return otherobj

    """Methods for inernal use"""

    def _get_index_anchor(self, reftype: str, refval: str) -> tuple[str, str]:
        """
        Return the docname and anchor name of index page. Can be used for ``make_refnode()``.

        .. warning:: This is no public API of sphinx and may broken in future version.
        """
        domain = self.name
        index = self.indices_for_reftype[reftype]
        return f'{domain}-{index.name}', index.indexer.anchor(refval)


# =============================
# Directive/Roles implementions
# =============================


class ObjDefineDirective(StrictDataDefineDirective):
    @override
    def process_pending_node(self, n: pending_node) -> bool:
        if n.template == self.template:
            n.hook_rendered_node(self._setup_objdesc)

        return super().process_pending_node(n)

    def _setup_objdesc(self, pending: pending_node, rendered: rendered_node) -> None:
        """Wrap rendered.children into ObjectDescription.

        TODO: considier inherit from ObjectDescription directive?

        Before::

            <rendered_node>
                <...> # children

        After::

            <rendered_node>
                <desc>
                  <desc_signature>
                      <desc_name>
                          <pending_node> # header, wait for rendering
                  <desc_content>
                      <...> # the original children
        """

        domain, objtype = self._get_obj_domain_and_type()

        def update_domaon_atts(node: nodes.Element):
            """Attach domain related info to node."""
            node['domain'] = domain.name
            # 'desctype' is a backwards compatible attribute
            node['objtype'] = node['desctype'] = objtype
            node['classes'].extend([domain.name, objtype])

        if (hdrtmpl := domain.templates[objtype].header) is None:
            # No header template available, no need to generate objdesc.
            update_domaon_atts(rendered)
            return

        # Queue a rendering for header, and setup anchor when rendering done.
        hdrnode = pending_node(pending.data, hdrtmpl, inline=True)
        hdrnode.hook_rendered_node(self._setup_objdesc_anchor)
        self.queue_pending_node(hdrnode)

        # Construct ObjectDescription.
        signode = addnodes.desc_signature('', '', addnodes.desc_name('', '', hdrnode))
        contnode = addnodes.desc_content('', *rendered.children)
        descnode = addnodes.desc('', signode, contnode)
        update_domaon_atts(descnode)

        # Add descnode as child of rendered.
        rendered.clear()
        rendered += descnode

    def _setup_objdesc_anchor(
        self, pending: pending_node, rendered: rendered_node
    ) -> None:
        domain, objtype = self._get_obj_domain_and_type()

        ahrnode = find_parent(pending, addnodes.desc_signature)
        assert ahrnode
        obj = rendered.data
        assert isinstance(obj, ParsedData)

        objids = get_object_uniq_ids(self.schema, obj)
        ahrterm = ValueWrapper(objids[0]).as_str() if objids else None
        ahrid = make_id(self.env, self.state.document, prefix=objtype, term=ahrterm)

        ahrnode['ids'].append(ahrid)
        # Add object name to node's names attribute.
        # 'names' is space-separated list containing normalized reference
        # names of an element.
        ahrnode['names'].extend(
            [nodes.fully_normalize_name(x) for x in ValueWrapper(objids).as_str_list()]
        )

        self.state.document.note_explicit_target(ahrnode)
        otherobj = domain.note_object(self.env.docname, ahrid, objtype, obj)

        if otherobj:
            report = Report(
                'Duplicate identifier',
                'INFO',
                source=pending.source,
                line=pending.line,
            )
            report.text(
                f'Duplicate object identifier at {self.env.docname}#{ahrid}, '
                f'other object at {otherobj[0]}#{otherobj[1]}'
            )
            report.code(pformat(otherobj[2]), lang='python')

            ahrnode += report.problematic((self.state.document, ahrnode.parent))
            blkparent = find_nearest_block_element(ahrnode) or self.state.document
            blkparent += report

    def _get_obj_domain_and_type(self) -> tuple[ObjDomain, str]:
        domainname, objtype = self.name.split(':', 1)
        _domain = self.env.get_domain(domainname)
        return cast(ObjDomain, _domain), objtype


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
        singleidx: dict[Category, dict[Category, set[PlainValue]]] = {}
        # Dual index for generating entrie (subtype=1) and its sub-entries (subtype=2).
        # Main category  →  Sub-Category →  Extra (for ordering objids) →  objids
        dualidx: dict[Category, dict[Category, dict[Category, set[PlainValue]]]] = {}

        objrefs = sorted(self.domain.references.items())
        for (objtype, objfield, objref), objids in objrefs:
            if objtype != self.reftype.objtype:
                continue
            if self.reftype.field and objfield != self.reftype.field:
                continue

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

        content: dict[Category, list[IndexEntry]] = {}  # category → entries
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
        self,
        objid: PlainValue,
        ignore_docnames: Iterable[str] | None,
        category: Category,
    ) -> IndexEntry | None:
        docname, anchor, obj = self.domain.objects[self.reftype.objtype, objid]
        if ignore_docnames and docname not in ignore_docnames:
            return None
        name = get_object_title(obj) or ValueWrapper._strify(objid)  # FIXME:
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


DEFAULT_INDEXER = LiteralIndexer()

INDEXER_REGSITRY: dict[str, Indexer] = {
    'lit': DEFAULT_INDEXER,
    'literal': DEFAULT_INDEXER,
    'slash': PathIndexer('/', 2),
    'year': YearIndexer(),
    'month': MonthIndexer(),
}

"""
sphinxnotes.any.domain
~~~~~~~~~~~~~~~~~~~~~~

Domain implementions.

:copyright: Copyright 2021 Shengyu Zhang
:license: BSD, see LICENSE for details.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, override, cast, TypeVar
from pprint import pformat

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx import addnodes
from sphinx.domains import Domain, ObjType, Index, IndexEntry
from sphinx.roles import XRefRole
from sphinx.util import logging
from sphinx.util.nodes import make_id, make_refnode
from sphinx.errors import ExtensionError
from sphinxnotes.render import (
    Phase,
    PlainValue,
    Template,
    ValueWrapper,
    ParsedData,
    Schema,
    PendingContext,
    ResolvedContext,
    pending_node,
    BaseContextDirective,
    UnparsedData,
    StrictDataDefineDirective,
)
from sphinxnotes.render.utils import (
    Report,
    find_nearest_block_element,
    find_parent,
    find_titular_node_upward,
)

from .obj import (
    Object,
    RefType,
    ObjTypeDef,
    Templates,
    Category,
    Indexer,
    get_object_title,
    get_object_uniq_ids,
    get_object_refs,
)
from .utils import strip_rst_markups
from .indexers import LiteralIndexer, PathIndexer, YearIndexer, MonthIndexer

if TYPE_CHECKING:
    from typing import Iterator, Iterable, Callable, Literal
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
            todocname, anchor = self._get_index_anchor(typ, target, location=node)
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

    """Public methods."""

    @classmethod
    def add_objtype(cls, objtype: str, typedef: ObjTypeDef) -> None:
        schema = typedef.schema
        tmpls = typedef.templates

        cls.schemas[objtype] = schema
        cls.templates[objtype] = tmpls

        # Create directive ``.. objtype::`` for documenting object.
        if typedef.auto:
            cls.directives[objtype] = AutoObjDefineDirective.derive(
                objtype,
                schema,
                tmpls.obj,
            )
        else:
            cls.directives[objtype] = ObjDefineDirective.derive(
                objtype,
                schema,
                tmpls.obj,
            )

        # Create directive ``.. objtype+embed::`` for embedding object.
        cls.directives[objtype + '+embed'] = ObjEmbedDirective

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
            mkindex(reftypes[0], DEFAULT_INDEXER)

        # Create {field,indexer}-specificed role and index.
        for name, field in schema.fields():
            if field.ref:
                reftype = RefType(objtype, name)
                reftypes.append(reftype)
                mkrole(reftype)  # create a role to reference object(s)
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

    def get_rendered_object(self, objtype: str, objid: PlainValue) -> list[nodes.Node]:
        docname, anchor, _ = self.objects[objtype, objid]
        doctree = self.env.get_doctree(docname)
        ahrnode = doctree.ids[anchor]
        if isinstance(ahrnode, addnodes.desc_signature):
            return [ahrnode.parent]
        assert False  # TODO: mark obj start and objend

    """Methods for inernal use"""

    def _get_index_anchor(
        self, reftype: str, refval: str, location=None
    ) -> tuple[str, str]:
        """
        Return the docname and anchor name of index page. Can be used for ``make_refnode()``.

        .. warning:: This is no public API of sphinx and may broken in future version.
        """
        domain = self.name
        index = self.indices_for_reftype[reftype]
        try:
            anchor = index.indexer.anchor(refval)
        except Exception as e:
            anchor = ''
            logger.warning(
                f'failed to convert {repr(refval)} (xref target) to anchor: {e}',
                location=location,
            )

        return f'{domain}-{index.name}', anchor


# =============================
# Directive/Roles implementions
# =============================


class ObjDefineDirective(StrictDataDefineDirective):
    """
    Directive for registering new objects in the domain.
    Handles ``.. any:objtype::``-like directives and creates object descriptions
    (descnode) with anchors.
    """

    """Methods that override from parent."""

    @override
    def process_pending_node(self, n: pending_node) -> bool:
        if n.template == self.template:
            n.hook_rendered_nodes(self.setup_objdesc)
        return super().process_pending_node(n)

    """Helpers methods for self and subclasses."""

    def get_domain_and_type(self) -> tuple[ObjDomain, str]:
        domainname, _, objtype = self.name.partition(':')
        _domain = self.env.get_domain(domainname)
        return cast(ObjDomain, _domain), objtype

    def setup_objdesc(self, pending: pending_node, rendered: list[nodes.Node]) -> None:
        """Wrap rendered nodes into ObjectDescription.

        Before::

            <nodes...> # the pass-in argument: ``rendered: list[nodes.Node]``

        After::

            <desc>
              <desc_signature>
                  <desc_name>
                      <pending_node> # header, wait for rendering
              <desc_content>
                  <nodes...> # the original ``rendered``
        """
        domain, objtype = self.get_domain_and_type()

        if (hdrtmpl := domain.templates[objtype].header) is None:
            # No header template available, no need to generate objdesc.
            return
        if (
            isinstance(pending.ctx, ParsedData)
            and pending.ctx.name is None
            and '{{ name }}' in hdrtmpl.text
        ):
            # HACK: do not generate signode when name is not given.
            return

        # Queue a rendering for header, and setup anchor when rendering done.
        hdrnode = pending_node(pending.ctx, hdrtmpl, inline=True)
        hdrnode.hook_rendered_nodes(self.setup_signode_anchor)
        self.queue_pending_node(hdrnode)

        # Construct ObjectDescription.
        signode = addnodes.desc_signature('', '', addnodes.desc_name('', '', hdrnode))
        contnode = addnodes.desc_content('', *rendered)
        descnode = addnodes.desc('', signode, contnode)
        self.update_domain_atts(descnode)

        # Replace the pass-in node list.
        rendered.clear()
        rendered.append(descnode)

    def update_domain_atts(self, node: nodes.Element):
        """Attach domain related info to node."""
        domain, objtype = self.get_domain_and_type()
        node['domain'] = domain.name
        # 'desctype' is a backwards compatible attribute
        node['objtype'] = node['desctype'] = objtype
        node['classes'].extend([domain.name, objtype])

    def setup_anchor(self, ahrnode: nodes.Element, obj: Object) -> None:
        domain, objtype = self.get_domain_and_type()

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
                source=ahrnode.source,
                line=ahrnode.line,
            )
            report.text(
                f'Duplicate object identifier at {self.env.docname}#{ahrid}, '
                f'other object at {otherobj[0]}#{otherobj[1]}'
            )
            report.code(pformat(otherobj[2]), lang='python')

            ahrnode += report.problematic((self.state.document, ahrnode.parent))
            blkparent = find_nearest_block_element(ahrnode) or self.state.document
            blkparent += report

    def setup_signode_anchor(
        self, pending: pending_node, rendered: list[nodes.Node]
    ) -> None:
        ahrnode = find_parent(pending, addnodes.desc_signature)
        assert ahrnode
        obj = pending.ctx
        assert isinstance(obj, ParsedData)

        self.setup_anchor(ahrnode, obj)


class AutoObjDefineDirective(ObjDefineDirective):
    """
    Directive that extends ObjDefineDirective that allows object to have
    header outside of object's nodes rather than a :cls:`addnodse.desc_signature`
    in :cls:`addnodes.desc`. For example, if we have the follow templates::

    .. code:: python

        # ...
        'obj': "Hi there, human! I am {{ name }}.",
        'header': 'This is {{ name }}',
        # ...

    Define a cat:

    .. code:: rst

        Mimi
        ====

        .. cat:: _

    The title "Mimi" will be used as cat's name, and the nodes.title will be
    rendered by cat's header template, the result will look like:

    .. code:: rst

        This is Mimi
        ============

        Hi there, human! I am mimi.
    """

    """Methods that override from parent."""

    @override
    @classmethod
    def derive(
        cls, name: str, schema: Schema, tmpl: Template
    ) -> type[StrictDataDefineDirective]:
        subcls = super().derive(name, schema, tmpl)
        if schema.name and schema.name.required:
            # data.name is resolved from external.
            subcls.required_arguments = 0
            subcls.optional_arguments = 1
        return subcls

    @override
    def process_pending_node(self, n: pending_node) -> bool:
        if n.template == self.template:
            n.hook_pending_context(self.setup_external_header)
            # Skip ObjDefineDirective.process_pending_node.
            return super(StrictDataDefineDirective, self).process_pending_node(n)

        return super().process_pending_node(n)

    """Helpers methods for self and subclasses."""

    def setup_external_header(
        self, pending: pending_node, ctx: PendingContext | ResolvedContext
    ) -> None:
        def fallback():
            # If we can not setup external header, fallback to setup objdesc.
            pending.hook_rendered_nodes(self.setup_objdesc)

        required, update_ctx_name = self.require_external_header(ctx)
        if required is not True:
            if required == 'Retry':
                pending.hook_resolved_context(self.setup_external_header)
            else:
                fallback()
            return
        assert update_ctx_name

        domain, objtype = self.get_domain_and_type()
        if (hdrtmpl := domain.templates[objtype].header) is None:
            fallback()
            return

        if not (header := self.resolve_external_header()):
            fallback()
            return

        # Update the name field in ctx.
        update_ctx_name(header.astext())

        hdrnode = pending_node(ctx, hdrtmpl, inline=True)
        hdrnode.hook_rendered_nodes(self.setup_external_header_anchor)
        self.queue_pending_node(hdrnode)

        # Replace header's children with pending node.
        header.clear()
        header += hdrnode

    def require_external_header(
        self, ctx: PendingContext | ResolvedContext
    ) -> tuple[Literal[True, False, 'Retry'], Callable[[str]] | None]:
        """
        Check whether the context require a external name.

        Returns:
            :Literal:
                :True:  Required
                :False: Don't required
                :Retry: Don't know yet, retry on ``hook_resolved_context`` plz.
            :Callable: A function for updating name, used by :meth:`_resolve_external_name`.
        """

        if isinstance(ctx, UnparsedData):
            # If the schema of RawData.name is a plain value (no a list)
            # and RawData.name is not given (None) or a underscore('_'),
            # we consider the object requires an external name.
            #
            # The special underscore is for compatible with sphinxnotes-any<3.
            # See also https://sphinx.silverrainz.me/any/tips.html#documenting-section-and-documentation
            if not ctx.schema.name or not ctx.schema.name.required:
                return False, None
            if ctx.schema.name.ctype is list and ctx.schema.name.etype is str:
                return 'Retry', None
            if ctx.schema.name.ctype is not None:
                return False, None
            if ctx.raw.name not in (None, '_'):
                return False, None

            def update_raw_name(name: str) -> None:
                ctx.raw.name = name

            return True, update_raw_name

        elif isinstance(ctx, ParsedData):
            # Most of the judgment is already done in the UnparseData branch.
            # When the ctx.name is a list[str] and the first element is '_',
            # we also consider it requires an external name.
            if (
                not isinstance(ctx.name, list)
                or len(ctx.name) == 0
                or ctx.name[0] != '_'
            ):
                return False, None

            def update_parsed_name(name: str) -> None:
                assert isinstance(ctx.name, list)
                ctx.name[0] = name

            return True, update_parsed_name

        return False, None

    def resolve_external_header(self) -> nodes.Element | None:
        domain, objtype = self.get_domain_and_type()

        if not (title := find_titular_node_upward(self.state.parent)):
            return None
        if 'any-header' in title['classes']:
            # Already header of other object.
            return None
        title['classes'].extend(
            set(['any', domain.name, 'any-header', objtype + '-header'])
        )
        return title

    def setup_external_header_anchor(
        self, pending: pending_node, rendered: list[nodes.Node]
    ) -> None:
        assert isinstance(pending.ctx, ParsedData)
        self.setup_anchor(pending.parent, pending.ctx)


@dataclass
class PendingObject(PendingContext):
    domain: ObjDomain
    objtype: str
    objid: str

    @override
    def resolve(self) -> ResolvedContext:
        _, _, obj = self.domain.objects[self.objtype, self.objid]
        return obj

    def __hash__(self) -> int:
        return hash((self.domain.name, self.objtype, self.objid))


class ObjEmbedDirective(BaseContextDirective):
    required_arguments = 1
    optional_arguments = 0
    option_spec = {
        'debug': directives.flag,
    }
    has_content = True

    def get_domain_and_type(self) -> tuple[ObjDomain, str]:
        domainname, _, dirname = self.name.partition(':')
        objtype, _, _ = dirname.partition('+')
        _domain = self.env.get_domain(domainname)
        return cast(ObjDomain, _domain), objtype

    def get_rendered_objects(self) -> list[nodes.Node]:
        domain, objtype = self.get_domain_and_type()
        objid = self.arguments[0]
        return domain.get_rendered_object(objtype, objid)

    """Methods that override from parent."""

    @override
    def current_context(self) -> PendingContext | ResolvedContext:
        domain, objtype = self.get_domain_and_type()
        objid = self.arguments[0]
        return PendingObject(domain, objtype, objid)

    @override
    def current_template(self) -> Template:
        if self.content:
            return Template(
                '\n'.join(self.content), Phase.Resolving, 'debug' in self.options
            )

        domain, objtype = self.get_domain_and_type()
        if tmpl := domain.templates[objtype].embed:
            return tmpl

        self.assert_has_content()
        assert False


# ==================
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

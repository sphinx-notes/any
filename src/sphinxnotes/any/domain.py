"""
sphinxnotes.any.domain
~~~~~~~~~~~~~~~~~~~~~~

Sphinx domain for describing anything.

:copyright: Copyright 2021 Shengyu Zhang
:license: BSD, see LICENSE for details.
"""

from __future__ import annotations
from typing import Any, Iterator, TYPE_CHECKING

from docutils.nodes import Element, literal, Text

from sphinx.addnodes import pending_xref
from sphinx.domains import Domain, ObjType
from sphinx.util import logging
from sphinx.util.nodes import make_refnode

from .schema import Schema, Object, PlainClassifier
from .directives import AnyDirective
from .roles import AnyRole
from .indices import AnyIndex

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.builders import Builder
    from sphinx.environment import BuildEnvironment
    from sphinx.util.typing import RoleFunction

logger = logging.getLogger(__name__)


class AnyDomain(Domain):
    """
    The Any domain for describing anything.
    """

    #: Domain name: should be short, but unique
    name: str = 'any'
    #: Domain label: longer, more descriptive (used in messages)
    label = 'Any'
    #: Type (usually directive) name -> ObjType instance
    object_types: dict[str, ObjType] = {}
    #: Directive name -> directive class
    directives: dict[str, type[AnyDirective]] = {}
    #: Role name -> role callable
    roles: dict[str, RoleFunction] = {}
    #: A list of Index subclasses
    indices: list[type[AnyIndex]] = []
    #: AnyDomain specific: type -> index class
    _indices_for_reftype: dict[str, type[AnyIndex]] = {}
    #: AnyDomain specific: type -> Schema instance
    _schemas: dict[str, Schema] = {}

    initial_data: dict[str, Any] = {
        # See property object
        'objects': {},
        # See property references
        'references': {},
    }

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
        objtype = obj.objtype
        _, objid = schema.identifier_of(obj)
        objrefs = schema.references_of(obj)
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

    # Override parent method
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

    # Override parent method
    def resolve_xref(
        self,
        env: BuildEnvironment,
        fromdocname: str,
        builder: Builder,
        typ: str,
        target: str,
        node: pending_xref,
        contnode: Element,
    ) -> Element | None:
        assert isinstance(contnode, literal)

        logger.debug('[any] resolveing xref of %s', (typ, target))
        objtype, objfield = reftype_to_objtype_and_objfield(typ)
        objids = set()
        if objfield:
            # NOTE: To prevent change domain data, dont use ``objids = xxx``
            ids = self.references.get((objtype, objfield, target))
            if ids:
                objids.update(ids)
        else:
            for (t, _, r), ids in self.references.items():
                if t == objtype and r == target:
                    objids.update(ids)

        schema = self._schemas[objtype]
        title = contnode[0].astext()
        has_explicit_title = node['refexplicit']
        newtitle = None

        if not objids:
            # The pending_xref node may be resolved by intersphinx,
            # so not emit warning here, see also warn_missing_reference.
            return None
        elif len(objids) == 1:
            todocname, anchor, obj = self.objects[objtype, objids.pop()]
            if not has_explicit_title:
                newtitle = schema.render_reference(obj)
        else:
            # Mulitple objects found, we should create link to indices page.
            (
                todocname,
                anchor,
            ) = self._get_index_anchor(typ, target)
            if not has_explicit_title:
                newtitle = schema.render_ambiguous_reference(title)
            logger.debug(
                f'ambiguous {objtype} {target} in {self}, '
                + f'ids: {objids} index: {todocname}#{anchor}'
            )

        if newtitle:
            logger.debug(f'[any] rewrite title from {title} to {newtitle}')
            contnode.replace(contnode[0], Text(newtitle))

        refnode = make_refnode(
            builder, fromdocname, todocname, anchor, contnode, objtype + ' ' + target
        )
        refnode['classes'] += [self.name, self.name + '-' + objtype]
        return refnode

    # Override parent method
    def get_objects(self) -> Iterator[tuple[str, str, str, str, str, int]]:
        for (objtype, objid), (docname, anchor, _) in self.data['objects'].items():
            yield objid, objid, objtype, docname, anchor, 1

    @classmethod
    def add_schema(cls, schema: Schema) -> None:
        # Add to schemas dict
        cls._schemas[schema.objtype] = schema

        reftypes = [schema.objtype]
        for name, field in schema.fields(all=False):
            if not field.ref:
                continue

            # Generates reftypes for all referenceable fields
            # For later use when generating roles and indices.
            reftype = objtype_and_objfield_to_reftype(schema.objtype, name)
            reftypes.append(reftype)

        for reftype in reftypes:
            _, field = reftype_to_objtype_and_objfield(reftype)
            # Create role for referencing object by field
            cls.roles[reftype] = AnyRole.derive(schema, field)(
                # Emit warning when missing reference (node['refwarn'] = True)
                warn_dangling=True,
                # Inner node (contnode) would be replaced in resolve_xref method,
                # so fix its class.
                innernodeclass=literal,
            )

            # FIXME: name and content can not be index now
            if field is not None:
                classifiers = schema.attrs[field].classifiers
            elif schema.name is not None:
                classifiers = schema.name.classifiers
            else:
                classifiers = [PlainClassifier()]
            # Generates index for indexing object by fields
            for indexer in classifiers:
                index = AnyIndex.derive(schema, field, indexer)
                cls.indices.append(index)
                cls._indices_for_reftype[reftype] = index  # TODO: mulitple catelogers.

        # TODO: document
        cls.object_types[schema.objtype] = ObjType(schema.objtype, *reftypes)
        # Generates directive for creating object.
        cls.directives[schema.objtype] = AnyDirective.derive(schema)

    def _get_index_anchor(self, reftype: str, refval: str) -> tuple[str, str]:
        """
        Return the docname and anchor name of index page. Can be used for ``make_refnode()``.

        .. warning:: This is no public API of sphinx and may broken in future version.
        """
        domain = self.name
        index = self._indices_for_reftype[reftype].name
        return f'{domain}-{index}', f'cap-{refval}'


def warn_missing_reference(
    app: Sphinx, domain: Domain, node: pending_xref
) -> bool | None:
    if domain and domain.name != AnyDomain.name:
        return None

    objtype, _ = reftype_to_objtype_and_objfield(node['reftype'])
    target = node['reftarget']

    msg = f'undefined {objtype}: {target}'
    logger.warning(msg, location=node, type='ref', subtype=objtype)
    return True


def reftype_to_objtype_and_objfield(reftype: str) -> tuple[str, str | None]:
    """Helper function for converting reftype(role name) to object infos."""
    v = reftype.split('.', maxsplit=1)
    return v[0], v[1] if len(v) == 2 else None


def objtype_and_objfield_to_reftype(objtype: str, objfield: str) -> str:
    """Helper function for converting object infos to reftype(role name)."""
    return objtype + '.' + objfield

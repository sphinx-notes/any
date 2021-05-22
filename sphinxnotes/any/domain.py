"""
    sphinxnotes.any.domain
    ~~~~~~~~~~~~~~~~~~~~~~

    Sphinx domain for describing anything.

    :copyright: Copyright 2021 Shengyu Zhang
    :license: BSD, see LICENSE for details.
"""

from __future__ import annotations
from typing import Tuple, Dict, Any, Iterator, Type, Set, List, TYPE_CHECKING

from docutils import nodes

from sphinx import addnodes
from sphinx.domains import Domain, ObjType
from sphinx.util import logging
from sphinx.util.nodes import make_refnode
if TYPE_CHECKING:
    from sphinx.builders import Builder
    from sphinx.environment import BuildEnvironment
    from sphinx.util.typing import RoleFunction

from .schema import Schema, Object
from .directives import AnyDirective
from .roles import AnyRole, objtype_and_objfield_to_reftype, reftype_to_objtype_and_objfield
from .indices import AnyIndex

logger = logging.getLogger(__name__)


class AnyDomain(Domain):
    """
    The Any domain for describing anything.
    """

    #: Domain name: should be short, but unique
    name:str = 'any'
    #: Domain label: longer, more descriptive (used in messages)
    label = 'Any'
    #: Type (usually directive) name -> ObjType instance
    object_types:Dict[str,ObjType]= {}
    #: Directive name -> directive class
    directives:Dict[str,Type[AnyDirective]] = {}
    #: Role name -> role callable
    roles:Dict[str,RoleFunction] = {}
    #: A list of Index subclasses
    indices:List[Type[AnyIndex]] = []            
    #: AnyDomain specific: Type -> index class
    _indices_for_reftype:Dict[str,Type[AnyIndex]] = {}

    initial_data:Dict[str,Any] = {
        # See property object
        'objects': {},
        # See property references
        'references': {}
    }

    @property
    def objects(self) -> Dict[Tuple[str,str], Tuple[str,str,Object]]:
        """(objtype, objid) -> (docname, anchor, obj)"""
        return self.data.setdefault('objects', {})

    @property
    def references(self) -> Dict[Tuple[str,str,str],Set[str]]:
        """(objtype, objfield, objref) -> set(objid)"""
        return self.data.setdefault('references', {})


    def note_object(self, docname:str, anchor:str, schema:Schema, obj:Object) -> None:
        objtype = obj.objtype
        _, objid = schema.identifier_of(obj)
        objrefs = schema.references_of(obj)
        if (objtype, objid) in self.objects:
            other_docname, other_anchor, other_obj = self.objects[objtype, objid]
            logger.warning(f'duplicate identifier of {obj} at {docname}#{anchor}' +
                           f'other object is {other_obj} at {other_docname}#{other_anchor}')
        logger.debug(f'[any] note object {objtype} {objid} at {docname}#{anchor}, references: {objrefs}')
        self.objects[objtype, objid] = (docname, anchor, obj)
        for objfield, objref in objrefs:
            self.references.setdefault((objtype, objfield, objref), set()).add(objid)


    # Override parent method
    def clear_doc(self, docname:str) -> None:
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
    def resolve_xref(self, env:BuildEnvironment, fromdocname:str,
                     builder:Builder, typ:str, target:str,
                     node:addnodes.pending_xref, contnode:nodes.Element) -> nodes.Element:
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
        if not objids:
            logger.warning(f'no such {objtype} {target} in {self}')
            return None
        elif len(objids) == 1:
            todocname, anchor, _ = self.objects[objtype, objids.pop()]
            return make_refnode(builder, fromdocname, todocname, anchor,
                                contnode, objtype + ' ' + target)
        else:
            todocname, anchor, = self._get_index_anchor(typ, target)
            logger.info(f'ambiguous {objtype} {target} in {self}, ' +
                        f'ids: {objids} index: {todocname}#{anchor}')
        return make_refnode(builder, fromdocname, todocname, anchor,
                            contnode, objtype + ' ' + target)


    # Override parent method
    def get_objects(self) -> Iterator[Tuple[str, str, str, str, str, int]]:
        for (objtype, objid), (docname, anchor, _) in self.data['objects'].items():
            yield objid, objid, objtype, docname, anchor, 1


    @classmethod
    def add_schema(cls, schema:Schema) -> None:
        # Generates reftypes(role names) for all referenceable fields
        reftypes = [schema.objtype]
        for name, field, _ in schema.fields_of(None):
            if field.referenceable:
                reftypes.append(objtype_and_objfield_to_reftype(schema.objtype, name))

        # Roles is used for converting role name to corrsponding objtype
        cls.object_types[schema.objtype] = ObjType(schema.objtype, *reftypes)
        cls.directives[schema.objtype] = AnyDirective.derive(schema)
        for r in reftypes:
            # Create role for referencing object (by various fields)
            _, field = reftype_to_objtype_and_objfield(r)

            cls.roles[r] = AnyRole.derive(schema, field)()

            index = AnyIndex.derive(schema, field)
            cls.indices.append(index)
            cls._indices_for_reftype[r] = index


    def _get_index_anchor(self, reftype:str, refval:str) -> Tuple[str,str]:
        """
        Return the docname and anchor name of index page. Can be used for ``make_refnode()``.

        .. warning:: This is no public API of sphinx and may broken in future version.
        """
        domain = self.name
        index = self._indices_for_reftype[reftype].name
        return f'{domain}-{index}', f'cap-{refval}'

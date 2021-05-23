"""
    sphinxnotes.any.roles
    ~~~~~~~~~~~~~~~~~~~~~

    Roles implementations.

    :copyright: Copyright 2021 Shengyu Zhang
    :license: BSD, see LICENSE for details.
"""
from __future__ import annotations
from typing import Tuple, Type, TYPE_CHECKING

from docutils import nodes

from sphinx.util import logging
from sphinx.roles import XRefRole
if TYPE_CHECKING:
    from sphinx.environment import BuildEnvironment

from .schema import Schema

logger = logging.getLogger(__name__)

class AnyRole(XRefRole):
    """
    XRefRole child class for referencing to anything. Not used directly,
    but dynamically subclassed to reference to specific .


    TODO: rst reference template
    """

    schema:Schema

    @classmethod
    def derive(cls, schema:Schema, field:str=None) -> Type["AnyRole"]:
        """Generate an AnyRole child class for referencing object."""
        return type('Any%s%sRole' % (schema.objtype.title(), field.title() if field else ''),
                    (cls,),
                    { 'schema': schema })


    def process_link(self, env:BuildEnvironment, refnode:nodes.Element,
                     has_explicit_title:bool, title:str, target:str) -> Tuple[str,str]:
        """Override parent method."""
        if has_explicit_title:
            # Don't apply any template if has_explicit_title
            return title, target

        domain = env.get_domain(refnode['refdomain'])
        objtype, objfield = reftype_to_objtype_and_objfield(refnode['reftype'])
        objids = set()
        if objfield:
            # NOTE: To prevent change domain data, dont use ``objids = xxx``
            ids = domain.data['references'].get((objtype, objfield, target))
            if ids:
                objids.update(ids)
        else:
            for (typ, _, ref), ids in domain.data['references'].items():
                if typ == objtype and ref == target:
                    objids.update(ids)
        logger.debug('[any] processing link get %d objects for target %s',
                     len(objids), target)
        if not objids:
            title = self.schema.render_missing_reference(title)
        elif len(objids) == 1:
            _, _, obj = domain.data['objects'][objtype, objids.pop()]
            title = self.schema.render_reference(obj)
        else:
            title = self.schema.render_ambiguous_reference(title)
        return title, target


def reftype_to_objtype_and_objfield(reftype:str) -> Tuple[str,str]:
    """Helper function for converting reftype(role name) to object infos."""
    reftype = reftype.split('.', maxsplit=1)
    return reftype[0], reftype[1] if len(reftype) == 2 else None


def objtype_and_objfield_to_reftype(objtype:str, objfield:str) -> str:
    """Helper function for converting object infos to reftype(role name)."""
    return objtype + '.' + objfield

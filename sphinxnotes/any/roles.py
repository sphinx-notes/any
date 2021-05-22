"""
    sphinxnotes.any.roles
    ~~~~~~~~~~~~~~~~~~~~~

    Roles implementations.

    :copyright: Copyright 2021 Shengyu Zhang
    :license: BSD, see LICENSE for details.
"""
from __future__ import annotations
from typing import Tuple, TYPE_CHECKING

from docutils import nodes

from sphinx.roles import XRefRole
from sphinx.util import logging
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

    def process_link(self, env:BuildEnvironment, refnode:nodes.Element,
                     has_explicit_title:bool, title:str, target:str) -> Tuple[str,str]:
        """Override parent method."""

        domain = env.get_domain(refnode['refdomain'])
        splited_reftype = refnode['reftype'].split('.', maxsplit=1)
        reftype = splited_reftype[0]
        reffield = splited_reftype[1] if len(splited_reftype) > 1 else None
        objids = set()
        for (objtype, objfield, objref), ids in domain.data['references'].items():
            if objtype != reftype:
                continue
            if reffield and objfield != reffield:
                continue
            if objref == target:
                objids = objids.union(ids)
        if not objids:
            logger.warning(f'no such {reftype} {target} in {domain}')
            if has_explicit_title:
                title = f'{title} (no {reftype} named {target})'
            else:
                title = f'{title} (no such {reftype})'
        elif len(objids) == 1:
            # Rewrite object referencee to object id
            target = objids.pop()
            _, _, obj = domain.data['objects'][reftype, target]
            title = self.schema.render_reference(obj, title if has_explicit_title else None)
        else:
            raise NotImplementedError
        return title, target

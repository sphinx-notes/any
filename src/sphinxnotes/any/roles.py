"""
sphinxnotes.any.roles
~~~~~~~~~~~~~~~~~~~~~

Roles implementations.

:copyright: Copyright 2021 Shengyu Zhang
:license: BSD, see LICENSE for details.
"""

from __future__ import annotations

from sphinx.util import logging
from sphinx.roles import XRefRole

from .schema import Schema

logger = logging.getLogger(__name__)


class AnyRole(XRefRole):
    """
    XRefRole child class for referencing to anything. Not used directly,
    but dynamically subclassed to reference to specific .


    TODO: rst reference template
    """

    schema: Schema # FIXME: not used

    @classmethod
    def derive(cls, schema: Schema, field: str | None = None) -> type['AnyRole']:
        """Generate an AnyRole child class for referencing object."""
        # TODO: field: Field
        return type(
            'Any%s%sRole' % (schema.objtype.title(), field.title() if field else ''),
            (cls,),
            {'schema': schema},
        )

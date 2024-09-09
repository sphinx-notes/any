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

logger = logging.getLogger(__name__)


class AnyRole(XRefRole):
    """
    XRefRole child class for referencing to :cls:`.schema.Object`.
    Not used directly, but dynamically subclassed to reference to specific
    objtype.
    """

    # NOTE: derive is not necessary for now.
    # @classmethod
    # def derive(cls) -> type['AnyRole']:
    #     pass

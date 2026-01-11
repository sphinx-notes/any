"""
sphinxnotes.obj
~~~~~~~~~~~~~~~

Sphinx extension entrypoint.

:copyright: Copyright 2020~2026 Shengyu Zhang
:license: BSD, see LICENSE for details.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from sphinxnotes.data import Schema

from .domain import ObjDomain
from .obj import Templates
from . import meta

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.config import Config
    from sphinx.util import logging

logger = logging.getLogger(__name__)


def _config_inited(app: Sphinx, config: Config) -> None:
    ObjDomain.name = config.obj_domain_name

    # Add schema before registering domain
    for objtype, d in app.config.obj_defines.items():
        # TODO: parse error
        schema= Schema.from_dsl(d['name'], d['attrs'], d['content'])
        ObjDomain.add_object_type(objtype, schema, Templates())

    app.add_domain(ObjDomain)


def setup(app: Sphinx):
    """Sphinx extension entrypoint."""
    meta.pre_setup(app)

    app.setup_extension('sphinxnotes.data')

    app.add_config_value('obj_domain_name', 'obj', 'env', types=str)
    app.add_config_value('obj_defines', [], 'env', types=dict)
    # TODO: parse obj define

    app.connect('config-inited', _config_inited)

    from . import dump
    dump.setup(app)

    return meta.post_setup(app)

"""
sphinxnotes.obj
~~~~~~~~~~~~~~~

Sphinx extension entrypoint.

:copyright: Copyright 2020~2026 Shengyu Zhang
:license: BSD, see LICENSE for details.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from sphinx.errors import ConfigError
from sphinx.util import logging
from sphinxnotes.data import Schema

from schema import Schema as DictSchema, SchemaError as DictSchemaError, Optional, Or

from . import meta
from .obj import Templates, ObjTypeDef
from .domain import ObjDomain

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.config import Config

logger = logging.getLogger(__name__)

OBJTYPE_DEFINE = DictSchema(
    {
        'schema': {
            Optional('name', default='str, required, uniq, ref'): Or(str, type(None)),
            Optional('attrs', default={}): {str: str},
            Optional('content', default='str'): Or(str, type(None)),
        },
        'templates': {
            Optional('obj', default='{{ content }}'): str,
            Optional('header', default='{{ name }}'): Or(str, type(None)),
            Optional('ref', default='{{ name }}'): str,
            Optional('ref_by', default={}): {str: str},
            Optional('embed', default=None): Or(str, type(None)),
        },
        Optional('auto', default=False): bool,
        Optional('debug', default=False): bool,
    }
)


def _validate_objtype_defines_dict(d: dict, config: Config) -> ObjTypeDef:
    objdef = OBJTYPE_DEFINE.validate(d)

    schemadef = objdef['schema']
    schema = Schema.from_dsl(
        schemadef['name'], schemadef['attrs'], schemadef['content']
    )

    tmplsdef = objdef['templates']
    tmpls = Templates(
        tmplsdef['obj'],
        tmplsdef['header'],
        tmplsdef['ref'],
        tmplsdef['ref_by'],
        tmplsdef['embed'],
        debug=objdef['debug'],
    )

    auto = objdef['auto'] or config.git_object_auto

    return ObjTypeDef(schema=schema, templates=tmpls, auto=auto)


def _config_inited(app: Sphinx, config: Config) -> None:
    ObjDomain.name = config.any_domain_name

    for objtype, objdef in app.config.any_object_types.items():
        # TODO: check ":" in objtype to support multiple domain
        try:
            objtypedef = _validate_objtype_defines_dict(objdef, config)
        except (DictSchemaError, ValueError) as e:
            raise ConfigError(
                f'Validating any_object_types[{repr(objtype)}]: {e}'
            ) from e
        ObjDomain.add_objtype(objtype, objtypedef)

    app.add_domain(ObjDomain)


def setup(app: Sphinx):
    """Sphinx extension entrypoint."""
    meta.pre_setup(app)

    app.setup_extension('sphinxnotes.data')

    app.add_config_value('any_domain_name', 'obj', 'env', types=str)
    app.add_config_value('any_object_types', {}, 'env', types=dict)
    app.add_config_value('git_object_auto', True, 'env', types=bool)

    app.connect('config-inited', _config_inited)

    from . import dump, datetime

    dump.setup(app)
    datetime.setup(app)

    return meta.post_setup(app)

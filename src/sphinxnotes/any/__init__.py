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

from sphinxnotes.data import Schema, Config as DataConfig

from schema import Schema as DictSchema, SchemaError as DictSchemaError, Optional

from . import meta
from .obj import Templates, IndexerRegistry
from .domain import ObjDomain
from .indexers import LiteralIndexer, PathIndexer, YearIndexer, MonthIndexer

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.config import Config

logger = logging.getLogger(__name__)

IndexerRegistry.update(
    {
        'lit': LiteralIndexer(),
        'literal': LiteralIndexer(),
        'slash': PathIndexer('/', 2),
        'year': YearIndexer(),
        'month': MonthIndexer(),
    }
)

OBJ_DEFINE_DICT_SCHEMA = DictSchema(
    {
        'schema': {
            Optional('name', default=None): str,
            'attrs': {str: str},
            Optional('content', default=None): str,
        },
        'templates': {
            'obj': str,
            'ref': str,
            Optional('ref_by', default={}): {str: str},
        },
    }
)


def _parse_obj_define_dict(d: dict) -> tuple[Schema, Templates]:
    objdef = OBJ_DEFINE_DICT_SCHEMA.validate(d)
    schemadef = objdef['schema']
    schema = Schema.from_dsl(
        schemadef['name'], schemadef['attrs'], schemadef['content']
    )

    tmplsdef = objdef['templates']
    tmpls = Templates(
        tmplsdef['obj'],
        tmplsdef['ref'],
        ref_by=tmplsdef['ref_by'],
        debug=DataConfig.template_debug,
    )

    return schema, tmpls


def _config_inited(app: Sphinx, config: Config) -> None:
    ObjDomain.name = config.obj_domain_name

    for objtype, objdef in app.config.obj_defines.items():
        # TODO: check ":" in objtype to support multiple domain

        try:
            schema, tmpls = _parse_obj_define_dict(objdef)
        except (DictSchemaError, ValueError) as e:
            raise ConfigError(f'{e}') from e

        ObjDomain.add_objtype(objtype, schema, tmpls)

    app.add_domain(ObjDomain)


def setup(app: Sphinx):
    """Sphinx extension entrypoint."""
    meta.pre_setup(app)

    app.setup_extension('sphinxnotes.data')

    app.add_config_value('obj_domain_name', 'obj', 'env', types=str)
    app.add_config_value('obj_defines', [], 'env', types=dict)

    app.connect('config-inited', _config_inited)

    from . import dump, datetime

    dump.setup(app)
    datetime.setup(app)

    return meta.post_setup(app)

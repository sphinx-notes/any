"""
sphinxnotes.any
~~~~~~~~~~~~~~~

Sphinx extension entrypoint.

:copyright: Copyright 2020 Shengyu Zhang
:license: BSD, see LICENSE for details.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import json
import dataclasses

from sphinx.util import logging

from .template import Environment as TemplateEnvironment
from .domain import AnyDomain, warn_missing_reference
from .objects import Schema
from . import meta

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.config import Config


logger = logging.getLogger(__name__)


def _config_inited(app: Sphinx, config: Config) -> None:
    AnyDomain.name = config.any_domain_name
    AnyDomain.label = config.any_domain_name

    # Add schema before registering domain
    for v in app.config.any_schemas:
        AnyDomain.add_schema(v)

    app.add_domain(AnyDomain)


def _on_build_finished(app: Sphinx, _):
    _dump_domain_data(app)


def _dump_domain_data(app: Sphinx):
    """Dump any domain data to a JSON file."""

    name = app.config.any_domain_name
    data = app.env.domaindata[name]
    objs = {}
    fn = f'{name}-objects.json'

    # sphinx.util.status_iterator alias has been deprecated since sphinx 6.1
    # and has been removed in sphinx 8.0
    try:
        from sphinx.util.display import status_iterator
    except ImportError:
        from sphinx.util import status_iterator

    for (objtype, objid), (docname, anchor, obj) in status_iterator(
        data['objects'].items(),
        f'dump {name} domain data to {fn}... ',
        'brown',
        len(data['objects']),
        0,
        stringify_func=lambda i: f'{i[0][0]}-{i[0][1]}',
    ):
        objs[f'{objtype}-{objid}'] = {
            'docname': docname,
            'anchor': anchor,
            'obj': dataclasses.asdict(obj),
        }

    with open(app.doctreedir.joinpath(fn), 'w') as f:
        f.write(json.dumps(objs, indent=2, ensure_ascii=False))


def setup(app: Sphinx):
    """Sphinx extension entrypoint."""
    meta.pre_setup(app)

    # Init template environment
    TemplateEnvironment.setup(app)

    app.add_config_value('any_domain_name', 'any', 'env', types=str)
    app.add_config_value('any_domain_dump', True, '', types=bool)
    app.add_config_value('any_schemas', [], 'env', types=list[Schema])

    app.connect('config-inited', _config_inited)
    app.connect('warn-missing-reference', warn_missing_reference)
    app.connect('build-finished', _on_build_finished)

    return meta.post_setup(app)

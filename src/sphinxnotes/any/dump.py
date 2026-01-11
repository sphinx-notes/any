"""
sphinxnotes.obj.dump
~~~~~~~~~~~~~~~~~~~~

Dump any domain data.

:copyright: Copyright 2026 Shengyu Zhang
:license: BSD, see LICENSE for details.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import json
import dataclasses

if TYPE_CHECKING:
    from sphinx.application import Sphinx

def _dump_domain_data(app: Sphinx, _):
    """Dump any domain data to a JSON file."""

    if not app.config.obj_domain_dump:
        return

    name = app.config.obj_domain_name
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
    app.add_config_value('obj_domain_dump', True, '', types=bool)
    app.connect('build-finished', _dump_domain_data)

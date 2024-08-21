"""
sphinxnotes.any
~~~~~~~~~~~~~~~

Sphinx extension entrypoint.

:copyright: Copyright 2020 Shengyu Zhang
:license: BSD, see LICENSE for details.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from sphinx.util import logging

from .template import Environment as TemplateEnvironment
from .domain import AnyDomain, warn_missing_reference
from .schema import Schema, Field, DateClassifier

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.config import Config

__version__ = '2.3.1'

logger = logging.getLogger(__name__)

# Re-Export
Field = Field
Schema = Schema
DateClassifier = DateClassifier


def _config_inited(app: Sphinx, config: Config) -> None:
    AnyDomain.name = config.any_domain_name
    AnyDomain.label = config.any_domain_name

    # Add schema before registering domain
    for v in app.config.any_schemas:
        AnyDomain.add_schema(v)

    app.add_domain(AnyDomain)


def setup(app: Sphinx):
    """Sphinx extension entrypoint."""

    # Init template environment
    TemplateEnvironment.setup(app)

    app.add_config_value('any_domain_name', 'any', 'env', types=str)
    app.add_config_value('any_schemas', [], 'env', types=list[Schema])
    app.connect('config-inited', _config_inited)
    app.connect('warn-missing-reference', warn_missing_reference)

    return {'version': __version__}

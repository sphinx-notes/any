"""
    sphinxnotes.any
    ~~~~~~~~~~~~~~~

    Sphinx extension entrypoint.

    :copyright: Copyright 2020 Shengyu Zhang
    :license: BSD, see LICENSE for details.
"""

from __future__ import annotations
from typing import List, TYPE_CHECKING

from sphinx.util import logging
if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.config import Config

from .template import Environment as TemplateEnvironment
from .domain import AnyDomain
from .schema import Schema, Field

__title__= 'sphinxnotes-any'
__license__ = 'BSD',
__version__ = '2.0a2'
__author__ = 'Shengyu Zhang'
__url__ = 'https://sphinx-notes.github.io/any'
__description__ = 'Sphinx Domain for describing Anything'
__keywords__ = 'documentation, sphinx, extension'

logger = logging.getLogger(__name__)

# Export
Field = Field
Schema = Schema

def _config_inited(app:Sphinx, config:Config) -> None:
    AnyDomain.name = config.any_domain_name
    AnyDomain.label = config.any_domain_name

    # Add schema before registering domain
    for v in app.config.any_schemas:
        AnyDomain.add_schema(v)

    app.add_domain(AnyDomain)


def setup(app:Sphinx) -> None:
    """Sphinx extension entrypoint."""

    # Init template environment
    TemplateEnvironment.setup(app)

    app.add_config_value('any_domain_name', 'any', 'env', types=str)
    app.add_config_value('any_schemas', [], 'env', types=List[Schema])
    app.connect('config-inited', _config_inited)

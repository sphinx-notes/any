"""
    sphinxnotes.any
    ~~~~~~~~~~~~~~~

    Sphinx extension entrypoint.

    :copyright: Copyright 2020 Shengyu Zhang
    :license: BSD, see LICENSE for details.
"""

from sphinx.util import logging

from sphinxnote.anything import AnyDomain, Template

# For type annotation
if True:
    from sphinx.application import Sphinx
    from sphinx.config import Config

logger = logging.getLogger(__name__)

def _config_inited(app:Sphinx, config:Config) -> None:
    for t in config.any_templates:
        directive, role, index = t.generate_domain_objects()
        app.add_directive_to_domain('any', t.name, directive)
        app.add_role_to_domain('any', t.name, role())
        if index:
            app.add_index_to_domain('any', t.name, index)

def setup(app:Sphinx):
    app.add_domain(AnyDomain)

    app.add_config_value('any_templates', [], '')
    app.connect('config-inited', _config_inited)

"""
sphinxnotes.jinja
~~~~~~~~~~~~~~~~~

Sphinx extension entrypoint of sphinxnotes-jinja.

:copyright: Copyright 2024 Shengyu Zhang
:license: BSD, see LICENSE for details.
"""

from importlib.metadata import version
from sphinx.application import Sphinx
from .context import ContextRole, ContextDirective

def setup(app: Sphinx):
    """Sphinx extension entrypoint."""

    app.add_role('test', ContextRole.derive('test'))
    app.add_directive('test', ContextDirective.derive('test', required_arguments=1, has_content=True))

    return {'version': version('sphinxnotes.any')}

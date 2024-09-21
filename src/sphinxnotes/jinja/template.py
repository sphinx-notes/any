
from typing import Any, Type
from textwrap import dedent

from sphinx.util.docutils import SphinxDirective, SphinxRole

import jinja2

class Environment(jinja2.Environment):
    pass

def render(cls: Type[SphinxRole] | Type[SphinxDirective], ctx: dict[str, Any]):
    env = Environment()
    if cls is SphinxDirective:
        template = dedent("""
                          {{ args[0] }}
                          ==============================================

                          {{ content }}
                          """)
    else:
        template = "<{{ text }}>"

    return env.from_string(template).render(ctx)

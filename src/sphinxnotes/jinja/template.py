
from typing import Any, Type
from textwrap import dedent

from sphinx.util.docutils import SphinxDirective, SphinxRole

import jinja2

class Environment(jinja2.Environment):
    pass

def render(obj: SphinxDirective | SphinxRole, ctx: dict[str, Any]):
    env = Environment()
    print('type', obj)
    if isinstance(obj, SphinxDirective):
        print('>>>>>>>>>>>>>> is dir')
        template = dedent("""
                          {{ args[0] }}
                          ==============================================

                          {{ content }}
                          """)
    if isinstance(obj, SphinxRole):
        print('>>>>>>>>>>>>>> is role')
        template = "<{{ text }}>"

    return env.from_string(template).render(ctx)

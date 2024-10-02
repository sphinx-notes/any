
from typing import Any, Type
from textwrap import dedent

from docutils import nodes
from sphinx.util.docutils import SphinxDirective, SphinxRole

import jinja2

class Environment(jinja2.Environment):
    pass

def render(obj: SphinxDirective | SphinxRole, ctx: dict[str, Any]):
    env = Environment()
    # env.filters['node_astext'] = node_astext
    print('type', obj)
    if isinstance(obj, SphinxDirective):
        print('>>>>>>>>>>>>>> is dir')
        template = """
txt::
    {% for line in doc.lines %}
    {{ line}}
    {%- endfor %}

dom::

    {% for line in doc.dom.split('\n') -%}
    {{ line }}
    {% endfor %}

title::
    {{ doc.title.text }}
"""
    if isinstance(obj, SphinxRole):
        print('>>>>>>>>>>>>>> is role')
        template = "<<{{ rst.text }}>>"

    return env.from_string(template).render(ctx)

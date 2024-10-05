
from typing import Any, Type
from textwrap import dedent

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective, SphinxRole

import jinja2

class Environment(jinja2.Environment):
    pass

def render(obj: SphinxDirective | SphinxRole, ctx: dict[str, Any]):
    env = Environment()
    # env.filters['node_astext'] = node_astext
    if isinstance(obj, SphinxDirective):
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
    {{ doc.section.title.text }}
"""
    if isinstance(obj, SphinxRole):
        print('>>>>>>>>>>>>>> is role')
        template = "<<{{ rst.text }}>>"

    return env.from_string(template).render(ctx)

class TemplateDirective(SphinxDirective):
    required_arguments = 0 
    optional_arguments = 1 
    final_argument_whitespace = False
    option_spec = {
        'extra': directives.unchanged,
    }
    has_content = True

    def run(self) -> list[nodes.Node]:
        ctx = {}
        for ctxname in self.arguments:
            ctx = {
                ctxname: context.load(ctxname)
            }

        text = template.render(self, ctx)

        return self.parse_text_to_nodes(text, allow_section_headings=True)


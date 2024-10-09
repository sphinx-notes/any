from typing import Type, Callable, Any

from docutils.nodes import Node
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective

from . import template

class ContextDirective(SphinxDirective):
    @classmethod
    def derive(cls, 
               directive_name: str,
               required_arguments: int = 0,
               optional_arguments: int = 0,
               final_argument_whitespace: bool = False,
               option_spec: list[str] | dict[str, Callable[[str], Any]] = {},
               has_content: bool = False) -> Type['ContextDirective']:
        """Generate directive class."""

        # If no conversion function provided in option_spec, fallback to directive.unchanged.
        if isinstance(option_spec, list):
            option_spec = {k: directives.unchanged for k in option_spec}

        return type(
            directive_name.title() + 'ContextDirective',
            (ContextDirective,),
            {
                # Member of docutils.parsers.rst.Directive.
                'required_arguments': required_arguments,
                'optional_arguments': optional_arguments,
                'final_argument_whitespace': final_argument_whitespace,
                'option_spec': option_spec,
                'has_content': has_content,
            },
        )


    def run(self) -> list[Node]:
        ctx = {}
        text = template.render(self, ctx)

        return self.parse_text_to_nodes(text, allow_section_headings=True)


class TemplateDirective(SphinxDirective):
    required_arguments = 0 
    optional_arguments = 10
    final_argument_whitespace = False
    option_spec = {}
    has_content = True

    def run(self) -> list[nodes.Node]:
        ctx = {}
        for ctxname in self.arguments:
            ctx = {
                ctxname: context.load(ctxname)
            }

        text = template.render(self, ctx)

        return self.parse_text_to_nodes(text, allow_section_headings=True)

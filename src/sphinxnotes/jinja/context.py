"""
sphinxnotes.jinja.context
~~~~~~~~~~~~~~~~~~~~~~~~~

Build :cls:`jinja2.runtime.Context` from reStructuredText.

context:

- env: Sphinx env
- doc: Current documentation
  doc.docname
  doc.section.title
- node: next, prev
- self $.name

:copyright: Copyright 2024 Shengyu Zhang
:license: BSD, see LICENSE for details.
"""

from __future__ import annotations
from typing import Type, Callable, Any

from docutils.nodes import Node, system_message, inline
from docutils.parsers.rst import directives, states
from sphinx.util.docutils import SphinxDirective, SphinxRole
from sphinx.util import logging

import .template

logger = logging.getLogger(__name__)


class RstContext(object):
    pass

class DocContext(object):
    pass

class EnvContext(object):
    pass


class ContextDirective(SphinxDirective):
    arguments_variable_name: str
    content_variable_name: str

    @classmethod
    def derive(cls, 
               directive_name: str,
               required_arguments: int = 0,
               optional_arguments: int = 0,
               final_argument_whitespace: bool = False,
               option_spec: list[str] | dict[str, Callable[[str], Any]] = {},
               has_content: bool = False,
               arguments_variable_name: str = 'args',
               content_variable_name: str = 'content') -> Type['ContextDirective']:
        # Generate directive class

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

                'arguments_variable_name': arguments_variable_name,
                'content_variable_name': content_variable_name,
            },
        )

    def run(self) -> list[Node]:
        ctx = {}
        if self.required_arguments + self.optional_arguments != 0:
            ctx[self.arguments_variable_name] = self.arguments
        if self.has_content:
            ctx[self.content_variable_name] = self.content
        for key in self.option_spec or {}:
            ctx[key] = self.options.get(key)
        
        text = template.render(type(self), ctx)

        return self.parse_text_to_nodes(text, allow_section_headings=True)


class ContextRole(SphinxRole):
    text_variable_name: str

    @classmethod
    def derive(cls, role_name: str, text_variable_name: str = 'text') -> Type['ContextRole']:
        # Generate sphinx role class
        return type(
            role_name.title() + 'ContextDirective',
            (ContextRole,),
            {
                'text_variable_name': text_variable_name,
            },
        )

    def run(self) -> tuple[list[Node], list[system_message]]:
        ctx = {
            self.text_variable_name: self.text,
        }

        text = template.render(type(self), ctx)

        parent = inline(self.rawtext, '', **self.options)
        memo = states.Struct(
            document=inliner.document, # type: ignore[attr-defined]
            reporter=inliner.reporter, # type: ignore[attr-defined]
            language=inliner.language) # type: ignore[attr-defined]
        return self.inliner.parse(text, self.lineno, memo, parent) # type: ignore[attr-defined]


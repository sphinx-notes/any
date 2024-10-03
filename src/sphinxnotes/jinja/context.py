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
from abc import ABC, abstractmethod

from docutils import nodes 
from docutils.nodes import Node, system_message, inline
from docutils.parsers.rst import directives, states
from sphinx.util.docutils import SphinxDirective, SphinxRole
from sphinx.util import logging

from . import template

logger = logging.getLogger(__name__)

class ContextGenerator(ABC):

    @abstractmethod
    def gen(self) -> dict[str, Any]:
        raise NotImplementedError()


class NodeAdapter(object):
    node: nodes.Node

    def __init__(self, n: nodes.Node):
        self.node = n

    @property
    def doc(self) -> NodeAdapter | None:
        """Return the current doctree root node."""
        if not self.node.document:
            return None
        return NodeAdapter(self.node.document)


    @property
    def section(self) -> NodeAdapter | None:
        """Return the current section."""
        sect = self.node.next_node(nodes.section, include_self=False, descend=False,
                            siblings=False, ascend=False)
        if not sect:
            return None
        return NodeAdapter(sect)

    @property
    def dom(self) -> str:
        return self.node.pformat()

    @property
    def lines(self) -> list[str]:
        return self.node.astext().split('\n')

    @property
    def text(self) -> str:
        return self.node.astext()

    @property
    def title(self) -> NodeAdapter | None:
        if not isinstance(self.node, (nodes.document, nodes.section)):
            print('node:', type(self.node), 'not doc sect')
            return None
        title = self.node.first_child_matching_class(nodes.title)
        if not title:
            print('no title')
            return None
        return NodeAdapter(self.node[title])


        
class TopLevelVarNames(object):
    env = 'env'
    doc = 'doc'
    self = 'self'
    super = 'super'
    git = 'git'

class _MarkupVars(object):
    name = 'name'
    rawtext = 'rawtext'
    source = 'source'
    lineno = 'lineno'

class _DirectiveVars(_MarkupVars):
    arguments = 'args'
    options = 'opts'
    content = 'content'


class RoleVars(_MarkupVars):
    content = 'content' 

class ContextDirective(SphinxDirective, ContextGenerator):
    @classmethod
    def derive(cls, 
               directive_name: str,
               required_arguments: int = 0,
               optional_arguments: int = 0,
               final_argument_whitespace: bool = False,
               option_spec: list[str] | dict[str, Callable[[str], Any]] = {},
               has_content: bool = False) -> Type['ContextDirective']:
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
            },
        )

    def gen(self) -> dict[str, Any]:
        source, lineno = self.get_source_info()
        ctx = {
            'name': self.name,
            'rawtext': self.block_text,
            'source': source,
            'lineno': lineno,
        }
        if self.required_arguments + self.optional_arguments != 0:
            ctx['args'] = self.arguments
        if self.has_content:
            ctx['content'] = self.content
        opts = ctx.setdefault('opts', {})
        for key in self.option_spec or {}:
            opts[key] = self.options.get(key)
        return ctx

        
    def run(self) -> list[Node]:
        ctx = {
            'rst': self.gen(),
            'env': self.env,
            'doc': NodeAdapter(self.state.document),
        }
        text = template.render(self, ctx)

        return self.parse_text_to_nodes(text, allow_section_headings=True)


class ContextRole(SphinxRole, ContextGenerator):
    text_variable_name: str

    @classmethod
    def derive(cls, role_name: str, text_variable_name: str = 'text') -> Type['ContextRole']:
        # Generate sphinx role class
        return type(
            role_name.title() + 'ContextRole',
            (ContextRole,),
            {
                'text_variable_name': text_variable_name,
            },
        )

    def gen(self) -> dict[str, Any]:
        source, lineno = self.get_source_info()
        ctx = {
            'content': self.text,
            'name': self.name,
            'rawtext': self.rawtext,
            'source': source,
            'lineno': lineno,
        }
        return ctx

    def run(self) -> tuple[list[Node], list[system_message]]:
        ctx = {
            'rst': self.gen(),
            'env': self.env,
            'doc': NodeAdapter(self.inliner.document),
        }

        text = template.render(self, ctx)

        parent = inline(self.rawtext, '', **self.options)
        memo = states.Struct(
            document=self.inliner.document, # type: ignore[attr-defined]
            reporter=self.inliner.reporter, # type: ignore[attr-defined]
            language=self.inliner.language) # type: ignore[attr-defined]
        return self.inliner.parse(text, self.lineno, memo, parent) # type: ignore[attr-defined]


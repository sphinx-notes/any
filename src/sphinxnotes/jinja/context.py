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
from typing import Any, TYPE_CHECKING
from abc import ABC, abstractmethod

from docutils import nodes 
from sphinx.util.docutils import SphinxDirective, SphinxRole
from sphinx.util import logging

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.environment import BuildEnvironment


logger = logging.getLogger(__name__)

class ContextGenerator(ABC):
    @abstractmethod
    def gen(self) -> dict[str, Any]:
        raise NotImplementedError()

_registry: dict[str, ContextGenerator] = {}

class SphinxContext(ContextGenerator):
    _env: BuildEnvironment

    def __init__(self, env: BuildEnvironment):
        self._env = env

    def gen(self) -> dict[str, Any]:
        return {
            'app': self._env.app,
            'env': self._env,
            'cfg': self._env.config,
            'builder': self._env.app.builder,
        }

class DocContext(ContextGenerator):
    _node: nodes.Node

    def __init__(self, node: nodes.Node):
        self._node = node

    def gen(self) -> dict[str, Any]:
        return {
            'root': self._node.document,
            'section': self._node.next_node(nodes.section,include_self=False, descend=False,
                            siblings=False, ascend=False)
        }

class SourceContext(ContextGenerator):
    _markup: SphinxDirective | SphinxRole

    def __init__(self, markup: SphinxDirective | SphinxRole):
        self._markup = markup

    def gen(self) -> dict[str, Any]:
        if isinstance(self._markup, SphinxDirective):
            rawtext = self._markup.block_text
        elif isinstance(self._markup, SphinxRole):
            rawtext = self._markup.rawtext
        else:
            raise ValueError()

        source, lineno = self._markup.get_source_info()
        return {
            'name': self._markup.name,
            'rawtext': rawtext,
            'source': source,
            'lineno': lineno,
        }


class DirectiveContext(ContextGenerator):
    _dir: SphinxDirective

    def __init__(self, dir: SphinxDirective):
        self._dir = dir

    def gen(self) -> dict[str, Any]:
        ctx: dict[str,Any] = {
            'opts': {},
        }
        if self._dir.required_arguments + self._dir.optional_arguments != 0:
            ctx['args'] = self._dir.arguments
        if self._dir.has_content:
            ctx['content'] = self._dir.content # TODO: StringList
        for key in self._dir.option_spec or {}:
            ctx['opts'][key] = self._dir.options.get(key)
        return ctx


class RoleContext(ContextGenerator):
    _role: SphinxRole

    def __init__(self, role: SphinxRole):
        self._role = role

    def gen(self) -> dict[str, Any]:
        return {
            'content': self._role.text,
        }

def _load_single_ctx(env: BuildEnvironment, ctxname: str) -> dict[str, Any]:
    if ctxname == 'sphinx':
        return SphinxContext(env).gen()
    elif ctxname == 'doc':
        return DocContext(env).gen()


def load_and_fuse(
    buildenv: BuildEnvironment,
    fuse_ctxs: list[str],
    separate_ctxs: list[str],
    allow_duplicate: bool = False) -> dict[str, Any]:




from typing import Type

from docutils.nodes import Node, system_message, inline
from docutils.parsers.rst import states
from sphinx.util.docutils import SphinxRole

from . import template

class ContextRole(SphinxRole):
    @classmethod
    def derive(cls, role_name: str) -> Type['ContextRole']:
        # Generate sphinx role class
        return type(
            role_name.title() + 'ContextRole',
            (ContextRole,),
            {},
        )

    def run(self) -> tuple[list[Node], list[system_message]]:
        ctx = {}
        text = template.render(self, ctx)

        parent = inline(self.rawtext, '', **self.options)
        memo = states.Struct(
            document=self.inliner.document, # type: ignore[attr-defined]
            reporter=self.inliner.reporter, # type: ignore[attr-defined]
            language=self.inliner.language) # type: ignore[attr-defined]
        return self.inliner.parse(text, self.lineno, memo, parent) # type: ignore[attr-defined]

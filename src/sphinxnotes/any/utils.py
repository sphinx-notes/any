import re

from docutils import nodes, core
from docutils.parsers.rst import roles


# TODO: remove
def strip_rst_markups(rst: str) -> str:
    """Strip markups and newlines in rST.

    .. warning: To make parsing success and no any side effects, we created a
    standalone rst praser, without any sphinx stuffs. Some many role functions
    registered by Sphinx (and Sphinx extension) will failed, so we remove all
    local (non-docutls builtin) role functions away from registry.
    While parsing role, these role functions will not be called because parser
    doesn't know it, and parser will generates nodes.problematic for unknown role.

    ..warning:: This function is not parallel-safe."""

    # Save and erase local roles.
    #
    # FIXME: sphinx.util.docutils.docutils_namespace() is a good utils to erase
    # and recover roles, but it panics Sphinx.
    # https://github.com/sphinx-doc/sphinx/issues/8978
    #
    # TODO: deal with directive.
    _roles, roles._roles = roles._roles, {}  # type: ignore[attr-defined]
    try:
        # https://docutils.sourceforge.io/docs/user/config.html
        settings = {
            'report_level': 4,  #  suppress error log
        }
        doctree = core.publish_doctree(rst, settings_overrides=settings)
        for n in doctree.findall(nodes.system_message):
            # Replace all system_message nodes.
            nop = nodes.literal('', ids=n.get('ids'))
            n.replace_self(nop)
        for n in doctree.findall(nodes.problematic):
            # Replace all problematic nodes and strip the role markups.
            if isinstance(n[0], nodes.Text):
                # :role:`text` →  text
                match = re.search(r'`([^`]+)`', n[0])
                if not match:
                    continue
                result = match.group(1)
                n.replace(n[0], nodes.Text(result))
        txt = doctree.astext()
    except Exception:
        txt = rst
    finally:
        # Recover local roles.
        roles._roles = _roles  # type: ignore[attr-defined]

    return txt

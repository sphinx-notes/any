"""
    sphinxnotes.any.directives
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Directive implementations.

    :copyright: Copyright 2021 Shengyu Zhang
    :license: BSD, see LICENSE for details.
"""
from __future__ import annotations
from typing import Dict, List, Type

from docutils import nodes
from docutils.statemachine import StringList
from docutils.parsers.rst import directives
from docutils.nodes import whitespace_normalize_name, fully_normalize_name

from sphinx import addnodes
from sphinx.util.docutils import SphinxDirective
from sphinx.util.nodes import make_id, nested_parse_with_titles
from sphinx.util import logging

from .schema import Schema, Object

logger = logging.getLogger(__name__)

class AnyDirective(SphinxDirective):
    """
    Directive to describe anything.  Not used directly,
    but dynamically subclassed to describe specific object.

    The class is modified from sphinx.directives.ObjectDescription
    """

    schema:Schema = None

    # Member of parent
    has_content:bool = True
    required_arguments:int = 0
    optional_arguments:int = 0
    final_argument_whitespace:bool = True
    option_spec:Dict[str,callable] = {}

    @classmethod
    def derive(cls, schema:Schema) -> Type["AnyDirective"]:
        """Generate an AnyDirective child class for describing object."""
        has_content = schema.content is not None

        if not schema.name:
            required_arguments = 0
            optional_arguments = 0
        elif schema.name.required:
            required_arguments = 1
            optional_arguments = 0
        else:
            required_arguments = 0
            optional_arguments = 1

        option_spec = {}
        for name, field in schema.attrs.items():
            if field.required:
                option_spec[name] = directives.unchanged_required
            else:
                option_spec[name] = directives.unchanged

        # Generate directive class
        return type('Any%sDirective' % schema.objtype.title(),
                    (AnyDirective,),
                    {'schema': schema,
                     'has_content': has_content,
                     'required_arguments': required_arguments,
                     'optional_arguments': optional_arguments,
                     'option_spec': option_spec, })


    def _build_object(self) -> Object:
        """Build object information for template rendering."""
        return self.schema.object(name=self.arguments[0] if self.arguments else None,
                                  attrs=self.options,
                                  # Convert docutils.statemachine.ViewList.data -> str
                                  content='\n'.join(list(self.content.data)))


    def _setup_nodes(self, obj:Object,
                   sectnode:nodes.Node,
                   ahrnode:nodes.Node,
                   contnode:nodes.Node) -> None:
        """
        Attach necessary informations to nodes.

        The necessary information contains: domain info, basic attributes for nodes
        (ids, names, classes...), name of anchor, description content and so on.

        :param sectnode: Section node, used as container of the whole object description
        :param ahrnode: Anchor node, used to mark the location of object description
        :param contnode: Content node, which contains the description content
        """
        domainname, objtype = self.name.split(':', 1)
        domain = self.env.get_domain(domainname)

        # Attach domain related info to section node
        sectnode['domain'] = domain.name
        # 'desctype' is a backwards compatible attribute
        sectnode['objtype'] = sectnode['desctype'] = objtype
        sectnode['classes'].append(domain.name)

        # Setup anchor
        _, objid = self.schema.identifier_of(obj)
        ahrid = make_id(self.env, self.state.document, prefix=objtype, term=objid)
        ahrnode['ids'].append(ahrid)
        # Add object name to node's names attribute.
        # 'names' is space-separated list containing normalized reference
        # names of an element.
        name = self.schema.name_of(obj)
        if isinstance(name, str):
            ahrnode['names'].append(fully_normalize_name(name))
        elif isinstance(name, list):
            ahrnode['names'].extend([fully_normalize_name(x) for x in name])
        self.state.document.note_explicit_target(ahrnode)
        # Note object by docu fields
        # FIXME: Cast to AnyDomain
        domain.note_object(self.env.docname, ahrid, self.schema, obj)

        # Parse description
        nested_parse_with_titles(self.state,
                                 StringList(self.schema.render_description(obj)),
                                 contnode)


    def _run_section(self, obj:Object) -> List[nodes.Node]:
        # Get the title of the "section" where the directive is located
        sectnode = self.state.parent
        titlenode = sectnode.next_node(nodes.title)
        if not titlenode or titlenode.parent != sectnode:
            # Title should be direct child of section
            sm = nodes.system_message('Failed to get title of current section',
                                      type='WARNING', level=2, backrefs=[])
            sectnode += sm
            title = ''
        else:
            title = titlenode.astext()
        # Replace "_" with section titl
        # FIXME: it is dirty
        obj.name = title + obj.name[1:]
        self._setup_nodes(obj, sectnode, sectnode, sectnode)
        # Add all content to existed section, so return nothing
        return []


    def _run_objdesc(self, obj:Object) -> List[nodes.Node]:
        descnode = addnodes.desc()
        # Generate signature node
        title = self.schema.title_of(obj)
        if title is None:
            # Use non-generated object ID as replacement of title
            idfield, objid = self.schema.identifier_of(obj)
            if idfield is not None:
                # ID is not generated
                title = objid
            else:
                # ID is auto-generated, Use '' is better than None
                title = ''
        signode = addnodes.desc_signature(title, '')
        signode += addnodes.desc_name(title, title)
        descnode.append(signode)
        # Generate content node
        contnode = addnodes.desc_content()
        descnode.append(contnode)
        self._setup_nodes(obj, descnode, signode, contnode)
        return [descnode]


    def run(self) -> List[nodes.Node]:
        obj = self._build_object()
        if self.schema.title_of(obj) == '_':
            # If no argument is given, or the first argument is '_',
            # use the section title as object name and anchor,
            # append content nodes to section node
            return self._run_section(obj)
        else:
            # Else, create Sphinx ObjectDescription(sphinx.addnodes.dsec_*)
            return self._run_objdesc(obj)

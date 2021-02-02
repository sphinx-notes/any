"""
    sphinxnotes.any
    ~~~~~~~~~~~~~~~

    Sphinx domain for describing anything.

    :copyright: Copyright 2020 Shengyu Zhang
    :license: BSD, see LICENSE for details.
"""

from __future__ import annotations
from typing import Tuple, Dict, Optional, Any, Iterator, Type, List, TYPE_CHECKING

from docutils.parsers.rst import directives
from docutils import nodes
from docutils.statemachine import StringList

from sphinx import addnodes
from sphinx.domains import Domain, ObjType
from sphinx.roles import XRefRole
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective
from sphinx.util.nodes import make_refnode, make_id, nested_parse_with_titles
if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.config import Config
    from sphinx.builders import Builder
    from sphinx.domains import Index
    from sphinx.environment import BuildEnvironment

if TYPE_CHECKING:
    from jinja2 import Template

from .template import Environment as TemplateEnvironment
from . import perset

logger = logging.getLogger(__name__)

tmplenv:TemplateEnvironment = None

class AnyDirective(SphinxDirective):
    """
    Directive to describe anything.  Not used directly,
    but dynamically subclassed to describe specific object.

    The class is modified from sphinx.directives.ObjectDescription
    """

    has_content:bool = True
    required_arguments:int = 0
    optional_arguments:int = 1
    final_argument_whitespace:bool = True
    option_spec:Dict[str,callable] = {}

    schema = None

    def _build_objinfo(self) -> Dict[str,Any]:
        """Build object information for template rendering."""

        schema = self.schema
        m:Dict[str,Any] = {}
        if self.arguments:
            m['names'] = [x.strip() for x in self.arguments[0].split('\n')]
        else:
            # Make sure key exists
            m['names'] = []
        m['content'] = self.content.data # docutils.statemachine.ViewList.data:List[str]
        if schema.id_field and self.options.get(schema.id_field):
            m[schema.id_field] = self.options.get(schema.id_field)
        for field in schema.other_fields:
            if self.options.get(field):
                m[field] = self.options.get(field)
        return m


    def _setup_nodes(self, objinfo:Dict[str,Any],
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
        name = objinfo['names'][0]

        # Attach domain related info to section node
        sectnode['domain'] = domain.name
        # 'desctype' is a backwards compatible attribute
        sectnode['objtype'] = sectnode['desctype'] = objtype
        sectnode['classes'].append(domain.name)

        # Setup anchor
        node_id = make_id(self.env, self.state.document, objtype, name)
        ahrnode['ids'].append(node_id)
        ahrnode['names'].append(name)
        self.state.document.note_explicit_target(ahrnode)
        if self.schema.id_field and objinfo[self.schema.id_field]:
            # Note object by ID
            domain.note_object(objtype, objinfo[self.schema.id_field],
                               node_id, objinfo, location=ahrnode)
        for n in objinfo['names']:
            # Note object by name and aliases
            domain.note_object(objtype, n, node_id, objinfo, location=ahrnode)

        # Parse content
        content = self.schema.content_template.render(objinfo)
        logger.debug('render directive template %s: %s',
                    self.schema.content_template, content)
        nested_parse_with_titles(self.state,
                                 StringList(content.split('\n')),
                                 contnode)


    def _run_section(self, objinfo:Dict[str,Any]) -> List[nodes.Node]:
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
        # Use title as object name
        objinfo['names'] = [title] + objinfo['names']
        self._setup_nodes(objinfo, sectnode, sectnode, sectnode)
        # Add all content to existed section, so return nothing
        return []


    def _run_objdesc(self, objinfo:Dict[str,Any]) -> List[nodes.Node]:
        name = objinfo['names'][0]
        descnode = addnodes.desc()
        # Generate signature node
        signode = addnodes.desc_signature(name, '')
        signode += addnodes.desc_name(name, name)
        descnode.append(signode)
        # Generate content node
        contnode = addnodes.desc_content()
        descnode.append(contnode)
        self._setup_nodes(objinfo, descnode, signode, contnode)
        return [descnode]


    def run(self) -> List[nodes.Node]:
        objinfo = self._build_objinfo()
        if not objinfo['names'] or objinfo['names'][0] == '_':
            # If no argument is given, or the first argument is '_',
            # use the section title as object name and anchor,
            # append content nodes to section node
            objinfo['names'] = objinfo['names'][1:]
            return self._run_section(objinfo)
        else:
            # Else, create Sphinx ObjectDescription(sphinx.addnodes.dsec_*)
            return self._run_objdesc(objinfo)


class AnyRole(XRefRole):
    """
    XRefRole child class for referencing to anything. Not used directly,
    but dynamically subclassed to reference to specific object.
    """

    schema = None

    def process_link(self, env:BuildEnvironment, refnode:nodes.Element,
                     has_explicit_title:bool, title:str, target:str) -> Tuple[str,str]:
        """See XRefRole.process_link."""

        domain = env.get_domain(refnode['refdomain'])
        objtype = refnode['reftype']
        a, b, objinfo = domain.objects.get((objtype, target), (None, None, None))
        if not objinfo:
            logger.warning('no such %s %s in %s' % (objtype, target, domain),
                           location=refnode)
            return (title, target)

        objinfo_with_title = objinfo.copy()
        if not has_explicit_title and title not in objinfo['names']:
            # Reference by object ID, replace it with object name
            objinfo_with_title['title'] = objinfo['names'][0]
            logger.debug('replace id %s with name %s' % (title, objinfo['names'][0]))
        else:
            objinfo_with_title['title'] = title
        title = self.schema.ref_template.render(objinfo_with_title)
        logger.debug('render role template %s: %s', self.schema.ref_template, title)
        return title, target

# TODO: AnyIndex


class Schema(object):
    """
    Schema holds description meta information of specific object,
    and able to dynamically generate corresponding directive, role and index
    for describing, referencing, and indexing specific object.
    """

    # Object type that the schema descripts
    type:str = None

    # Special optional fields, Field name of unique object ID
    id_field:Optional[str] = None
    # Other regular fields
    other_fields:List[str] = []

    # Templates
    ref_template:Template = None
    # Templates
    content_template:Template = None

    @classmethod
    def from_config(cls, config:Dict[str,Any]) -> 'Schema':
        """ Constructor by giving a config. """

        # Deal with '' for special fields
        id_field = config['fields'].get('id')
        if id_field == '':
            id_field = 'id'

        return Schema(config['type'],
                      config['fields'].get('others'),
                      id_field = id_field,
                      ref_template = config['templates'].get('reference'),
                      content_template = config['templates'].get('content'))

    def __init__(self, type:str,
                 other_fields:List[str],
                 id_field:Optional[str]=None,
                 ref_template:str='{{ title }}',
                 content_template:str='{{ content }}'):
        self.type = type
        self.other_fields = other_fields
        self.id_field = id_field
        self.ref_template = tmplenv.from_string(ref_template)
        self.content_template = tmplenv.from_string(content_template)


    def generate_directive(self) -> Type[AnyDirective]:
        """Generate an AnyDirective child class for describing object."""

        option_spec = {}
        for field in self.other_fields:
            option_spec[field] = directives.unchanged
        if self.id_field:
            option_spec[self.id_field] = directives.unchanged_required

        # Generate directive class
        return type('Any%sDirective' % self.type.title(),
                    (AnyDirective,),
                    { 'schema': self, 'option_spec': option_spec, })


    def generate_role(self) -> Type[AnyRole]:
        """Generate an AnyRole child class for referencing object."""
        return type('Any%sRole' % self.type.title(),
                    (AnyRole,),
                    { 'schema': self })


    def generate_index(self) -> Type[Index]:
        """TODO."""
        return None


class AnyDomain(Domain):
    """
    The Any domain for describing anything.
    """

    name = 'any'
    label = 'Anything'

    # Static class member for shareing information among all AnyDomain instance
    #
    # ref: https://stackoverflow.com/a/27568860
    _object_types:Dict[str,ObjType] = {}
    @property
    def object_types(self):
        return type(self)._object_types
    @object_types.setter
    def object_types(self, val):
        type(self)._object_types = val
    _directives:Dict[str,Type[AnyDirective]] = {} # directive name -> directive class
    @property
    def directives(self):
        return type(self)._directives
    @directives.setter
    def directives(self, val):
        type(self)._directives = val
    _roles:Dict[str,AnyRole] = {} # role name -> role callable
    @property
    def roles(self):
        return type(self)._roles
    @roles.setter
    def roles(self, val):
        type(self)._roles = val

    initial_data:Dict[str,Any] = {
        # See property object.
        'objects': {},
    }


    @property
    def objects(self) -> Dict[Tuple[str, str], Tuple[str, str, Dict[str,Any]]]:
        """(objtype, fullname) -> (docname, node_id, objinfo)"""
        return self.data.setdefault('objects', {})


    def note_object(self, objtype:str, name:str, node_id:str,
                    objinfo:Dict[str,Any], location:Any=None) -> None:
        if (objtype, name) in self.objects:
            docname, node_id, _ = self.objects[objtype, name]
            logger.warning('duplicate name/id of %s %s, other instance in %s' %
                           (objtype, name, docname), location=location)

        logger.debug('note %s %s: %s' % (objtype, name, objinfo), location=location)

        self.objects[objtype, name] = (self.env.docname, node_id, objinfo)


    def clear_doc(self, docname: str) -> None:
        for (typ, name), (doc, _, _) in list(self.objects.items()):
            if doc == docname:
                del self.objects[typ, name]


    def resolve_xref(self, env:BuildEnvironment, fromdocname:str,
                     builder:Builder, typ:str, target:str,
                     node:addnodes.pending_xref, contnode:nodes.Element) -> nodes.Element:
        objtypes = self.objtypes_for_role(typ)
        for objtype in objtypes:
            todocname, node_id, _ = self.objects.get((objtype, target), (None, None, None))
            if todocname:
                return make_refnode(builder, fromdocname, todocname, node_id,
                                    contnode, target + ' ' + objtype)
        return None


    def get_objects(self) -> Iterator[Tuple[str, str, str, str, str, int]]:
        for (typ, name), (docname, node_id, _) in self.data['objects'].items():
            yield name, name, typ, docname, node_id, 1


    @classmethod
    def add_schema(cls, schema) -> None:
        if cls._object_types.get(schema.type):
            logger.warning('schema %s already exists in %s, override it' %
                           (schema.type, cls))
        cls._directives[schema.type] = schema.generate_directive()
        cls._roles[schema.type] = schema.generate_role()()
        cls._object_types[schema.type] = ObjType(schema.type, schema.type)


def _config_inited(app:Sphinx, config:Config) -> None:
    perset_tbl = {
        'friend': perset.friend,
        'book': perset.book,
    }
    for v in config.any_schemas:
        if isinstance(v, str):
            v = perset_tbl[v]
        AnyDomain.add_schema(Schema.from_config(v))


def setup(app:Sphinx):
    """Sphinx extension entrypoint."""

    # Init template environment
    global tmplenv
    tmplenv = TemplateEnvironment(app)

    app.add_domain(AnyDomain)

    app.add_config_value('any_schemas', [], '')
    app.connect('config-inited', _config_inited)

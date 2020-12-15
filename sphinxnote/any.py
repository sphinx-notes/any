"""
    sphinxnotes.any
    ~~~~~~~~~~~~~~~

    Sphinx extension entrypoint.

    :copyright: Copyright 2020 Shengyu Zhang
    :license: BSD, see LICENSE for details.

"""

from typing import Tuple, Dict, Optional, Any, Iterator, Type, List

from docutils.parsers.rst import directives
from docutils import nodes
from docutils.statemachine import StringList

from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx import addnodes
from sphinx.builders import Builder
from sphinx.domains import Domain, ObjType, Index
from sphinx.environment import BuildEnvironment
from sphinx.roles import XRefRole
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective
from sphinx.util.nodes import make_refnode, make_id, nested_parse_with_titles

from jinja2 import Template


logger = logging.getLogger(__name__)


class AnyDirective(SphinxDirective):
    '''
    Directive to describe anything. Not used directly, but dynamically
    subclassed to add custom behavior.

    The class is modified from sphinx.directives.ObjectDescription
    '''

    has_content:bool = True
    required_arguments:int = 1
    optional_arguments:int = 0
    final_argument_whitespace:bool = True
    option_spec:Dict[str,callable] = {
        'noindex': directives.flag,
    }

    schema = None

    def _build_field_mapping(self) -> Dict[str,str]:
        ''' Build field mapping for template rendering. '''

        schema = self.schema
        m:Dict[str,str] = {}
        names = ['']
        _id = names[0] = m['name'] = self.arguments[0]
        m['content'] = self.content.data # docutils.statemachine.ViewList.data
        content = str(self.content)
        if schema.id_field and self.options.get(schema.id_field):
            _id = m[schema.id_field] = self.options.get(schema.id_field)
        if schema.alias_field and self.options.get(schema.alias_field):
            m[schema.alias_field] = self.options.get(schema.alias_field).split('\n')
        if schema.url_field and self.options.get(schema.url_field):
            m[schema.url_field] = self.options.get(schema.url_field)
        for field in schema.other_fields:
            if schema.options.get(field):
                m[field] = schema.options.get(field)
        return m


    def run(self) -> List[nodes.Node]:
        name = self.arguments[0]
        content = self.content.data # docutils.statemachine.ViewList.data

        indexnode = addnodes.index(entries=[])

        descnode = addnodes.desc()

        # Create signature
        signode = addnodes.desc_signature(name, '')
        descnode.append(descnode)
        signode += addnodes.desc_name(name, name)

        # Create content
        contentnode = addnodes.desc_content()
        descnode.append(contentnode)
        nested_parse_with_titles(self.state, content, contentnode)




        return []


class AnyRole(XRefRole):
    ''' XRefRole subclass for refering to anything. '''

    schema:Schema = None

    def process_link(self, env:BuildEnvironment, refnode:nodes.Element,
                     has_explicit_title:bool, title:str, target:str) -> Tuple[str,str]:
        ''' See XRefRole.process_link. '''

        return self._schema % title, target

# TODO: AnyIndex

class Schema(object):
    '''Schema for description of anything. TODO: link to page. '''

    name:str = None

    # Optional fields
    id_field:Optional[str] = None
    alias_field:Optional[str] = None
    url_field:Optional[str] = None
    other_fields:List[str] = []

    # Templates
    role_template:Template = None
    directive_template:Template = None

    @classmethod
    def from_config(cls, config:Dict[str,Any]) -> 'Schema':
        return Schema(config['name'],
                      config['fields'].get('id'),
                      config['fields'].get('alias'),
                      config['fields'].get('url'),
                      config['fields'].get('others'),
                      role_template = config['templates'].get('role_template'),
                      directive_template = config['templates'].get('directive_template'))

    def __init__(self, name:str,
                 id_field:Optional[str],
                 alias_field:Optional[str],
                 url_field:Optional[str],
                 other_fields:List[str],
                 role_template:str='{{name}}',
                 directive_template:str='{{content}}'):
        self.name = name
        self.alias_field = alias_field
        self.url_field  = url_field
        self.other_fields = other_fields
        self.role_template = Template(role_template)
        self.directive_template = Template(directive_template)


    def _build_directive(self) -> Type[AnyDirective]:
        ''' Dynamically create directive type for descripting object
        as required_arguments of schema. '''

        option_spec = {}
        if self.id_field:
            option_spec[self.id_field] = directives.unchanged
        if self.aliad_field:
            option_spec[self.alias_field] = directives.unchanged
        if self.url_field:
            option_spec[self.url_field] = directives.unchanged
        for field in self.other_fields:
            option_spec[field] = directives.unchanged

        # Create directive class
        return type('Any%sDirective' % self.name.title(),
                    (AnyDirective,),
                    {
                        'schema': self,
                        'option_spec': option_spec,
                    })


    def _build_role(self) -> Type[AnyRole]:
        ''' Dynamically create directive class for descripting object
        as requirements of schema. '''
        return type('Any%sRole' % self.name.title(),
                    (AnyRole,),
                    { 'schema': self })


    def _build_index(self) -> Optional[Type[Index]]:
        return None


    def build_domain_objects(self) -> Tuple[Type[AnyDirective],
                                            Type[AnyRole],
                                            Optional[Type[Index]]]:
        '''Dynamically create role type for referencing object as schema.'''

        return (self._build_directive(),
                self._build_role(),
                self._build_index())


    class AnyDomain(Domain):
        '''
        The Any domain for descripting anything.'''

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

            initial_data:Dict[str,Tuple[str,ObjType]] = { # fullname -> docname, objtype
                'objects': {}, 
            }

    @property
    def objects(self) -> Dict[Tuple[str, str], Tuple[str, str]]:
        return self.data.setdefault('objects', {}) # (objtype, fullname) -> (docname, node_id)

    def note_object(self, objtype:str, name:str, node_id:str, location:Any=None) -> None:
        print('note obj', objtype, name, node_id)
        if (objtype, name) in self.objects:
            docname, node_id = self.objects[objtype, name]
            logger.warning('duplicate description of %s %s, other instance in %s' %
                           (objtype, name, docname), location=location)

        self.objects[objtype, name] = (self.env.docname, node_id)


    def clear_doc(self, docname: str) -> None:
        for (typ, name), (doc, node_id) in list(self.objects.items()):
            if doc == docname:
                del self.objects[typ, name]


    def resolve_xref(self, env:BuildEnvironment, fromdocname:str, builder:Builder,
                     typ:str, target:str, node:pending_xref, contnode:Element) -> Element:
        objtypes = self.objtypes_for_role(typ)
        for objtype in objtypes:
            todocname, node_id = self.objects.get((objtype, target), (None, None))
            if todocname:
                return make_refnode(builder, fromdocname, todocname, node_id,
                                    contnode, target + ' ' + objtype)
        return None


    def get_objects(self) -> Iterator[Tuple[str, str, str, str, str, int]]:
        for (typ, name), (docname, node_id) in self.data['objects'].items():
            yield name, name, typ, docname, node_id, 1


    @classmethod
    def add_schema(cls, schema:Schema) -> None:
        if cls._object_types.get(schema.name):
            logger.warning('object %s already exists in %s, override it' %
                           (schema.name), cls)
        directive, role, _ = schema.build_domain_objects()
        cls._directives[schema.name] = directive
        cls._roles[schema.name] = role()
        cls._object_types[schema.name] = ObjType(schema.name, schema.name)


def _config_inited(app:Sphinx, config:Config) -> None:
    for c in config.any_schemas:
        t = Schema.from_config(c)
        AnyDomain.add_schema(t)


def setup(app:Sphinx):
    '''Sphinx extension entrypoint.'''

    app.add_domain(AnyDomain)
    print('reg domain')

    app.add_config_value('any_schemas', [], '')
    app.connect('config-inited', _config_inited)

"""
    sphinxnotes.any
    ~~~~~~~~~~~~~~~

    Sphinx extension entrypoint.

    :copyright: Copyright 2020 Shengyu Zhang
    :license: BSD, see LICENSE for details.
"""

from typing import Tuple, Dict, Optional, Any, Iterator, Type, List
from typing import cast

from docutils.parsers.rst import directives
from docutils.nodes import Element

from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx.addnodes import pending_xref, desc_name, desc_signature 
from sphinx.builders import Builder
from sphinx.directives import ObjectDescription
from sphinx.domains import Domain, ObjType, Index
from sphinx.environment import BuildEnvironment
from sphinx.roles import XRefRole
from sphinx.util import logging
from sphinx.util.nodes import make_refnode, make_id

    
logger = logging.getLogger(__name__)


class AnyDirective(ObjectDescription):
    '''
    Directive to describe anything. Not used directly, but dynamically
    subclassed to add custom behavior.
    '''

    def add_target_and_index(self, name:str, sig:str, signode:desc_signature) -> None:
        node_id = make_id(self.env, self.state.document, self.objtype, name)
        signode['ids'].append(node_id)

        self.state.document.note_explicit_target(signode)

        domain = cast(AnyDomain, self.env.get_domain('any'))
        domain.note_object(self.objtype, name, node_id, location=signode)


    def handle_signature(self, sig:str, signode:desc_signature) -> str:
        # Generate node for object name
        signode += desc_name(text=sig)
        return sig


class AnyRole(XRefRole):
    ''' XRefRole subclass for refering to anything. '''

    _template:str

    def process_link(self, env:BuildEnvironment, refnode:Element,
                     has_explicit_title:bool, title:str, target:str) -> Tuple[str,str]:
        '''
        Called after parsing title and target text, and creating the reference
        node (given in refnode). This method can alter the reference node and
        must return a new (or the same) (title, target) tuple.
        '''

        return self._template % title, target

# TODO: AnyIndex

class Template(object):
    '''Template for descripting anything.

    TODO: link to page
    '''

    @classmethod
    def from_config(cls, config:Dict[str,Any]) -> 'Template':
        return Template(config['name'],
                config['fields'].get('id'),
                config['fields'].get('alias'),
                config['fields'].get('url'),
                config['fields'].get('brief'),
                config['fields'].get('picture'),
                config['fields'].get('others'),
                role_title = config['templates'].get('role_title'),
                )

    def __init__(self, name:str,
            id_field:Optional[str],
            alias_field:Optional[str],
            url_field:Optional[str],
            brief_field:Optional[str],
            picture_field:Optional[str],
            other_fields:List[str],
            role_title:str='%s',
            directive_template:Any=None):
        self.name = name
        self._alias_field = alias_field
        self._url_field  = url_field
        self._brief_field = brief_field
        self._picture_field = picture_field
        self._other_fields = other_fields
        self._role_title = role_title
        self._directive_template = directive_template
        
    def _generate_directive(self) -> Type[AnyDirective]:
        '''Dynamically create Directive class awaiting for being added to Domain'''
        option_spec = {}
        if self._alias_field:
            option_spec[self._alias_field] = directives.unchanged
        if self._url_field:
            option_spec[self._url_field] = directives.uri
        if self._brief_field:
            option_spec[self._brief_field] = directives.path
        if self._picture_field:
            option_spec[self._brief_field] = directives.uri
        for field in self._other_fields:
            option_spec[field] = directives.unchanged

        # Create directive class
        return type(
                'Any%sDirective' % self.name.title(), # TODO: Class name validition
                (AnyDirective,), 
                { 'required_arguments': 1,
                    'option_spec': option_spec,
                    'has_content': True,})


    def _generate_role(self) -> Type[AnyRole]:
        return type(
                'Any%sRole' % self.name.title(), # TODO: Class name validition
                (AnyRole,), 
                { '_template': self._role_title,})


    def _generate_index(self) -> Optional[Type[Index]]:
        return None


    def generate_domain_objects(self) -> Tuple[Type[AnyDirective], Type[AnyRole], Optional[Type[Index]]]:
        '''Dynamically create classes that awaiting for being added to Domain'''

        return (self._generate_directive(), self._generate_role(), self._generate_index())

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

    def __init__(self, env):
        print('init')
        super(AnyDomain, self).__init__(env)

    def note_object(self, objtype:str, name:str, node_id:str, location:Any=None) -> None:
        if (objtype, name) in self.objects:
            docname, node_id = self.objects[objtype, name]
            logger.warning('duplicate description of %s %s, other instance in %s' %
                           (objtype, name, docname), location=location)

        self.objects[objtype, name] = (self.env.docname, node_id)


    def clear_doc(self, docname: str) -> None:
        '''
        Remove traces of a document in the domain-specific inventories.'''

        for (typ, name), (doc, node_id) in list(self.objects.items()):
            if doc == docname:
                del self.objects[typ, name]


    def resolve_xref(self, env:BuildEnvironment, fromdocname:str, builder:Builder,
                     typ:str, target:str, node:pending_xref, contnode:Element) -> Element:
        '''
        Resolve the pending_xref node with the given typ and target.

        This method should return a new node, to replace the xref node,
        containing the contnode which is the markup content of the cross-reference.

        If no resolution can be found, None can be returned;
        the xref node will then given to the ‘missing-reference’ event,
        and if that yields no resolution, replaced by contnode.

        The method can also raise sphinx.environment.NoUri to suppress the
        ‘missing-reference’ event being emitted.'''

        objtypes = self.objtypes_for_role(typ)
        for objtype in objtypes:
            todocname, node_id = self.objects.get((objtype, target), (None, None))
            if todocname:
                return make_refnode(builder, fromdocname, todocname, node_id,
                                    contnode, target + ' ' + objtype)
        return None


    def get_objects(self) -> Iterator[Tuple[str, str, str, str, str, int]]:
        '''
        Return an iterable of “object descriptions”, which are tuples with five items:

        name – fully qualified name
        dispname – name to display when searching/linking
        type – object type, a key in self.object_types
        docname – the document where it is to be found
        anchor – the anchor name for the object
        priority – how “important” the object is (determines placement in search results)
            1: default priority (placed before full-text matches)
            0: object is important (placed before default-priority objects)
            2: object is unimportant (placed after full-text matches)
            -1: object should not show up in search at all'''

        for (typ, name), (docname, node_id) in self.data['objects'].items():
            yield name, name, typ, docname, node_id, 1


    @classmethod
    def add_template(cls, template:Template) -> None:
        if cls._object_types.get(template.name):
            logger.warning('object %s already exists in %s, override it' %
                    (template.name), cls)
        directive, role, _ = template.generate_domain_objects()
        cls._directives[template.name] = directive
        cls._roles[template.name] = role()
        cls._object_types[template.name] = ObjType(template.name, template.name)


def _config_inited(app:Sphinx, config:Config) -> None:
    print('config inited')
    for c in config.any_templates:
        AnyDomain.add_template(Template.from_config(c))


def setup(app:Sphinx):
    '''Sphinx extension entrypoint.'''

    app.add_domain(AnyDomain)
    print('reg domain')

    app.add_config_value('any_templates', [], '')
    app.connect('config-inited', _config_inited)

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
from docutils.nodes import Element, Node, section, title
from docutils.statemachine import StringList

from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx.addnodes import pending_xref, desc, desc_name, desc_signature, desc_content, index
from sphinx.builders import Builder
from sphinx.domains import Domain, ObjType, Index
from sphinx.environment import BuildEnvironment
from sphinx.roles import XRefRole
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective
from sphinx.util.nodes import make_refnode, make_id
from sphinx.util.docfields import DocFieldTransformer, Field, TypedField

    
logger = logging.getLogger(__name__)

input = ['''You can adapt this file completely to your liking, but it should at least contain the root `toctree` directive.''']

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

    # Types of doc fields that this directive handles, see sphinx.util.docfields
    doc_field_types:List[Field] = []
    domain:str = None
    objtype:str = None
    indexnode:index = None

    def add_target_and_index(self, name: Any, sig: str, signode: desc_signature) -> None:
        """
        Add cross-reference IDs and entries to self.indexnode, if applicable.

        *name* is whatever :meth:`handle_signature()` returned.
        """
        return  # do nothing by default

    def run(self) -> List[Node]:
        """
        Main directive entry function, called by docutils upon encountering the
        directive.

        This directive is meant to be quite easily subclassable, so it delegates
        to several additional methods.  What it does:

        * find out if called as a domain-specific directive, set self.domain
        * create a `desc` node to fit all description inside
        * parse standard options, currently `noindex`
        * create an index node if needed as self.indexnode
        * parse all given signatures (as returned by self.get_signatures())
          using self.handle_signature(), which should either return a name
          or raise ValueError
        * add index entries using self.add_target_and_index()
        * parse the content and handle doc fields in it
        """
        if ':' in self.name:
            self.domain, self.objtype = self.name.split(':', 1)
        else:
            self.domain, self.objtype = '', self.name
        self.indexnode = index(entries=[])

        node = desc()
        node.document = self.state.document
        node['domain'] = self.domain
        node['objtype'] = self.objtype
        node['noindex'] = noindex = ('noindex' in self.options)
        if self.domain:
            node['classes'].append(self.domain)

        self.names = []
        sig = self.arguments[0]
        node.append(desc_name(text=sig))
        # if not noindex:
        #     self.add_target_and_index(sig, sig, signode)

        contentnode = desc_content()
        node.append(contentnode)
        if self.names:
            # needed for association of version{added,changed} directives
            self.env.temp_data['object'] = self.names[0]
        print('tttt', type(self.content))
        print('>>>>', self.content)
        self.state.nested_parse(StringList(initlist=input), self.content_offset, contentnode)
        return [self.indexnode, node]



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
            option_spec[self._picture_field] = directives.uri
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
        print('domain init')
        super(AnyDomain, self).__init__(env)

    def note_object(self, objtype:str, name:str, node_id:str, location:Any=None) -> None:
        print('note obj', objtype, name, node_id)
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

        print('resolve xref', fromdocname, typ, target)
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
        print(cls._directives)


def _config_inited(app:Sphinx, config:Config) -> None:
    print('config inited')
    for c in config.any_templates:
        t = Template.from_config(c)
        print('reg', t.name)
        AnyDomain.add_template(t)


def setup(app:Sphinx):
    '''Sphinx extension entrypoint.'''

    app.add_domain(AnyDomain)
    print('reg domain')

    app.add_config_value('any_templates', [], '')
    app.connect('config-inited', _config_inited)

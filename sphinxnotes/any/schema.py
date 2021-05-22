"""
    sphinxnotes.any.schema
    ~~~~~~~~~~~~~~~~~~~~~~

    Schema and object implementations.

    :copyright: Copyright 2021 Shengyu Zhang
    :license: BSD, see LICENSE for details.
"""
from typing import Tuple, Dict, Any, Iterator, List, Set, Optional
from enum import Enum, auto
from dataclasses import dataclass

from sphinx.util import logging

from .errors import AnyExtensionError
from .template import Environment as TemplateEnvironment   


logger = logging.getLogger(__name__)

class ObjectError(AnyExtensionError):
    pass

class SchemaError(AnyExtensionError):
    pass


@dataclass
class Object(object):
    objtype:str
    name:str
    attrs:Dict[str,str]
    content:str


@dataclass
class Field(object):

    class Form(Enum):
        PLAIN = auto()
        WORDS = auto()
        LINES = auto()

    form:Form=Form.PLAIN
    unique:bool=False
    referenceable:bool=False
    required:bool=False

    def __post_init__(self) -> None:
        # Unique field must be required
        if self.unique:
            if not self.required:
                raise SchemaError('Unique field must be required')
            if self.form != self.Form.PLAIN:
                raise SchemaError('Unique field must has PLAIN from')


    def as_plain(self, rawval:str) -> str:
        assert self.form == self.Form.PLAIN
        return rawval


    def as_words(self, rawval:str) -> List[str]:
        assert self.form == self.Form.WORDS
        return [x.strip() for x in rawval.split(' ') if x.strip() != '']


    def as_lines(self, rawval:str) -> List[str]:
        assert self.form == self.Form.LINES
        return [x.strip() for x in rawval.split('\n') if x.strip() != '']


    def value_of(self, rawval:Optional[str]) -> Any:
        if rawval is None:
            assert not self.required
            return None

        if self.form == self.Form.PLAIN:
            return self.as_plain(rawval)
        elif self.form == self.Form.WORDS:
            return self.as_words(rawval)
        elif self.form == self.Form.LINES:
            return self.as_lines(rawval)
        else:
            raise NotImplementedError


class Schema(object):
    """
    Schema describes a class of object, and be able to dynamically generate
    corresponding directive, role and index for describing, referencing,
    and indexing specific object.
    """

    # Class-wide shared Special keys used in template rendering context
    NAME_KEY = 'name'
    CONTENT_KEY = 'content'
    TITLE_KEY = 'title'

    # Object type
    objtype:str

    # Object fields
    name:Field
    attrs:Dict[str,Field]
    content:Field

    # Class-wide shared template environment
    # FIXME: can not save jinja template environment because the following error::
    #   Traceback (most recent call last):
    #     File "/usr/lib/python3.9/site-packages/sphinx/cmd/build.py", line 280, in build_main
    #       app.build(args.force_all, filenames)
    #     File "/usr/lib/python3.9/site-packages/sphinx/application.py", line 350, in build
    #       self.builder.build_update()
    #     File "/usr/lib/python3.9/site-packages/sphinx/builders/__init__.py", line 292, in build_update
    #       self.build(to_build,
    #     File "/usr/lib/python3.9/site-packages/sphinx/builders/__init__.py", line 323, in build
    #       pickle.dump(self.env, f, pickle.HIGHEST_PROTOCOL)
    #   _pickle.PicklingError: Can't pickle <function sync_do_first at 0x7f839bc9d790>: it's not the same object as jinja2.filters.sync_do_first
    description_template:str
    reference_template:str
    # TODO: index template

    def __init__(self, objtype:str,
                 name:Field=Field(unique=True, referenceable=True, required=True),
                 attrs:Dict[str,Field]={},
                 content:Field=Field(),
                 description_template:str='{{ content }}',
                 reference_template:str='{{ title }}') -> None:
        self.objtype = objtype
        self.name = name
        self.attrs = attrs
        self.content = content
        self.description_template = description_template
        self.reference_template = reference_template

        # Check attrs constraint
        has_unique = False
        for field in [self.name, self.content] + list(self.attrs.values()):
            if has_unique and field.unique:
                raise SchemaError('only one unique field is allowed in schema')
            else:
                has_unique = field.unique


    def object(self, name:Optional[str], attrs:Dict[str,str], content:Optional[str]) -> Object:
        """Generate a object"""
        obj = Object(objtype=self.objtype,
                     name=name,
                     attrs=attrs,
                     content=content)
        for name, field, rawval in self.fields_of(obj):
            if field.required and rawval is None:
                raise ObjectError('value of field {name} is none while it is required')
        return obj


    def fields_of(self, obj:Object) -> Iterator[Tuple[str,Field,str]]:
        """Helper method for returning all fields of object and its raw values"""
        if self.name:
            yield (self.NAME_KEY, self.name, obj.name if obj else None)
        for name, field in self.attrs.items():
            yield (name, field, obj.attrs.get(name) if obj else None)
        if self.content:
            yield (self.CONTENT_KEY, self.content, obj.content if obj else None)


    def name_of(self, obj:Object) -> Any:
        assert obj
        return self.content.value_of(obj.name)


    def attrs_of(self, obj:Object) -> Dict[str,Any]:
        assert obj
        attrs = {}
        for name, field in self.attrs.items():
            rawval = obj.attrs.get(name)
            attrs[name]= field.value_of(rawval)
        return attrs


    def content_of(self, obj:Object) -> Any:
        assert obj
        return self.content.value_of(obj.content)


    @staticmethod
    def _value_as_single(field:Field, rawval:str) -> str:
        """Helper method for getting value of field"""
        if field.form == Field.Form.PLAIN:
            return rawval
        elif field.form == Field.Form.WORDS:
            return field.as_words(rawval)[0]
        elif field.form == Field.Form.LINES:
            return field.as_lines(rawval)[0]


    @staticmethod
    def _value_as_list(field:Field, rawval:str) -> List[str]:
        """Helper method for getting value of field"""
        if field.form == Field.Form.PLAIN:
            return [rawval]
        elif field.form == Field.Form.WORDS:
            return field.as_words(rawval)
        elif field.form == Field.Form.LINES:
            return field.as_lines(rawval)


    def identifier_of(self, obj:Object) -> Optional[str]:
        """Return unique identifier of object. """
        assert obj
        for _, field, rawval in self.fields_of(obj):
            if field.unique:
                return self._value_as_single(field, rawval)
        return None


    def title_of(self, obj:Object) -> Optional[str]:
        """Return title (display name) of object."""
        assert obj
        if obj.name is None:
            return None
        return self._value_as_single(self.name, obj.name)


    def references_of(self, obj:Object) -> Set[Tuple[str,str]]:
        """Return all references (referenceable fields) of object"""
        assert obj
        refs = []
        for name, field, rawval in self.fields_of(obj):
            if field.referenceable:
                refs += [(name, x) for x in self._value_as_list(field, rawval)]
        return refs


    def render_description(self, obj:Object) -> List[str]:
        assert obj
        context = {
            self.NAME_KEY: self.name_of(obj),
            self.CONTENT_KEY: self.content_of(obj),
            **self.attrs_of(obj),
        }
        tmpl = TemplateEnvironment().from_string(self.description_template)
        description = tmpl.render(context)
        logger.debug('[any] render description template %s: %s' %
                    (self.description_template, description))
        return description.split('\n')


    def render_reference(self, obj:Object, explicit_title:str=None) -> str:
        assert obj
        context = {
            self.NAME_KEY: self.name_of(obj),
            self.CONTENT_KEY: self.content_of(obj),
            self.TITLE_KEY: explicit_title or self.title_of(obj),
            **self.attrs_of(obj),
        }
        tmpl = TemplateEnvironment().from_string(self.reference_template)
        reference = tmpl.render(context)
        logger.debug('[any] render references template %s: %s',
                    self.reference_template, reference)
        return reference

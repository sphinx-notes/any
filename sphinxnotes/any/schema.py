"""
    sphinxnotes.any.schema
    ~~~~~~~~~~~~~~~~~~~~~~

    Schema and object implementations.

    :copyright: Copyright 2021 Shengyu Zhang
    :license: BSD, see LICENSE for details.
"""
from typing import Tuple, Dict, Iterator, List, Set, Optional, Union
from enum import Enum, auto
from dataclasses import dataclass
import uuid

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
        pass


    def as_plain(self, rawval:str) -> str:
        assert self.form == self.Form.PLAIN
        assert rawval is not None
        return rawval


    def as_words(self, rawval:str) -> List[str]:
        assert self.form == self.Form.WORDS
        assert rawval is not None
        return [x.strip() for x in rawval.split(' ') if x.strip() != '']


    def as_lines(self, rawval:str) -> List[str]:
        assert self.form == self.Form.LINES
        assert rawval is not None
        return [x.strip() for x in rawval.split('\n') if x.strip() != '']


    def value_of(self, rawval:Optional[str]) -> Union[None,str,List[str]]:
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
    TYPE_KEY = 'type'
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
    missing_reference_template:str
    ambiguous_reference_template:str

    def __init__(self, objtype:str,
                 name:Field=Field(unique=True, referenceable=True),
                 attrs:Dict[str,Field]={},
                 content:Field=Field(),
                 description_template:str='{{ content }}',
                 reference_template:str='{{ title }}',
                 missing_reference_template:str='{{ title }} (missing reference)',
                 ambiguous_reference_template:str='{{ title }} (disambiguation)') -> None:
        self.objtype = objtype
        self.name = name
        self.attrs = attrs
        self.content = content
        self.description_template = description_template
        self.reference_template = reference_template
        self.missing_reference_template = missing_reference_template
        self.ambiguous_reference_template = ambiguous_reference_template

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
                raise ObjectError(f'value of field {name} is none while it is required')
        return obj


    def fields_of(self, obj:Object) -> Iterator[Tuple[str,Field,str]]:
        """Helper method for returning all fields of object and its raw values"""
        if self.name:
            yield (self.NAME_KEY, self.name, obj.name if obj else None)
        for name, field in self.attrs.items():
            yield (name, field, obj.attrs.get(name) if obj else None)
        if self.content:
            yield (self.CONTENT_KEY, self.content, obj.content if obj else None)


    def name_of(self, obj:Object) -> Union[None,str,List[str]]:
        assert obj
        return self.content.value_of(obj.name)


    def attrs_of(self, obj:Object) -> Dict[str,Union[str,List[str]]]:
        assert obj
        attrs = {}
        for name, field in self.attrs.items():
            rawval = obj.attrs.get(name)
            val = field.value_of(rawval)
            if val is not None:
                attrs[name]= val
        return attrs


    def content_of(self, obj:Object) -> Union[None,str,List[str]]:
        assert obj
        return self.content.value_of(obj.content)


    @staticmethod
    def _value_as_single(field:Field, rawval:str) -> str:
        """Helper method for getting value of field"""
        if field.form == Field.Form.PLAIN:
            return field.as_plain(rawval)
        elif field.form == Field.Form.WORDS:
            return field.as_words(rawval)[0]
        elif field.form == Field.Form.LINES:
            return field.as_lines(rawval)[0]


    @staticmethod
    def _value_as_list(field:Field, rawval:str) -> List[str]:
        """Helper method for getting value of field"""
        if field.form == Field.Form.PLAIN:
            return [field.as_plain(rawval)]
        elif field.form == Field.Form.WORDS:
            return field.as_words(rawval)
        elif field.form == Field.Form.LINES:
            return field.as_lines(rawval)


    def identifier_of(self, obj:Object) -> Tuple[Optional[str],str]:
        """
        Return unique identifier of object.
        If there is not any unique field, return (None, uuid[:7] instead.
        """
        assert obj
        for name, field, rawval in self.fields_of(obj):
            if not field.unique:
                continue
            if rawval is None:
                break
            return name, self._value_as_single(field, rawval)
        return None, uuid.uuid4().hex[:7]


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
            if not field.referenceable:
                continue
            if rawval is None:
                continue
            refs += [(name, x) for x in self._value_as_list(field, rawval)]
        return set(refs)


    def _context_without_object(self) -> Dict[str,Union[str,List[str]]]:
        return  {
            self.TYPE_KEY: self.objtype,
        }


    def _context_of(self, obj:Object) -> Dict[str,Union[str,List[str]]]:
        context = self._context_without_object()
        context.update({
            **self.attrs_of(obj),
        })

        def set_if_not_none(key:str, val:Union[str,List[str]]) -> None:
            if val is not None:
                context[key] = val
        set_if_not_none(self.NAME_KEY, self.name_of(obj))
        set_if_not_none(self.TITLE_KEY, self.title_of(obj))
        set_if_not_none(self.CONTENT_KEY, self.content_of(obj))

        return context


    def render_description(self, obj:Object) -> List[str]:
        assert obj
        tmpl = TemplateEnvironment().from_string(self.description_template)
        description = tmpl.render(self._context_of(obj))
        logger.debug('[any] render description template %s: %s' %
                    (self.description_template, description))
        return description.split('\n')


    def render_reference(self, obj:Object) -> str:
        assert obj
        tmpl = TemplateEnvironment().from_string(self.reference_template)
        reference = tmpl.render(self._context_of(obj))
        logger.debug('[any] render references template %s: %s',
                    self.reference_template, reference)
        return reference


    def _render_reference_without_object(self, explicit_title:str,
                                         reference_template:str) -> str:
        context = self._context_without_object()
        context[self.TITLE_KEY] = explicit_title
        tmpl = TemplateEnvironment().from_string(reference_template)
        reference = tmpl.render(context)
        logger.debug('[any] render references template without object %s: %s',
                    reference_template, reference)
        return reference


    def render_missing_reference(self, explicit_title:str) -> str:
        logger.debug('[any] render missing references template %s', explicit_title)
        return self._render_reference_without_object(
            explicit_title, self.missing_reference_template)


    def render_ambiguous_reference(self, explicit_title:str) -> str:
        logger.debug('[any] render ambiguous references template %s', explicit_title)
        return self._render_reference_without_object(
            explicit_title, self.ambiguous_reference_template)

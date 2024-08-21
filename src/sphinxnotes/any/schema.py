"""
sphinxnotes.any.schema
~~~~~~~~~~~~~~~~~~~~~~

Schema and object implementations.

:copyright: Copyright 2021 Shengyu Zhang
:license: BSD, see LICENSE for details.
"""

from typing import Iterator, Any, Iterable, Literal, TypeVar, Callable
import dataclasses
import pickle
import hashlib
from time import strptime
from abc import ABC, abstractmethod

from sphinx.util import logging

from .errors import AnyExtensionError
from .template import Environment as TemplateEnvironment


logger = logging.getLogger(__name__)


class ObjectError(AnyExtensionError):
    pass


class SchemaError(AnyExtensionError):
    pass


class Value(object):
    """ "An immutable optional :class:`Field`."""

    type T = None | str | list[str]
    _v: T

    def __init__(self, v: T):
        # TODO: type checking
        self._v = v

    @property
    def value(self) -> T:
        return self._v

    def as_list(self) -> list[str]:
        if isinstance(self._v, str):
            return [self._v]
        elif isinstance(self._v, list):
            return self._v
        else:
            return []

    def as_str(self) -> str:
        return str(self._v)


class Form(ABC):
    @abstractmethod
    def extract(self, raw: str) -> Value:
        """Extract :class:`Value` from field's raw value."""
        raise NotImplementedError


class Single(Form):
    def __init__(self, strip=False):
        self.strip = strip

    def extract(self, raw: str) -> Value:
        return Value(raw.strip() if self.strip else raw)


class List(Form):
    def __init__(self, sep: str, strip=False, max=-1):
        self.strip = strip
        self.sep = sep
        self.max = max

    def extract(self, raw: str) -> Value:
        strv = raw.split(self.sep, maxsplit=self.max)
        if self.strip:
            strv = [x.strip() for x in strv]
        return Value(strv)


@dataclasses.dataclass
class Classif(object):
    """
    Classification and sorting of an object, and generating
    py:cls:`sphinx.domain.IndexEntry`.

    :py:meth:`sphinx.domain.Index.generate` returns ``(content, collapse)``,
    and type of  ``contents`` is a list of ``(letter, IndexEntry list)``.
    letter is categoy of index entries, and some of index entries may be followed
    by sub-entries (distinguish by :py:attr:`~sphinx.domains.IndexEntry.subtype`).
    So Sphinx's index can represent up to 2 levels of indexing:

    :single index: letter -> normal entry
    :dual index:   letter -> entry with sub-entries -> sub-entry

    Classif can be used to generating all of 3 kinds of IndexEntry:

    :normal entry:            Classif(category=X)
    :entry with sub-entries:  Classif(category=X, entry=Y)
    :sub-entry:               Classif(category=X, entry=Y, subentry=Z)

    .. hint::

       In genindex_, the category is usually a single first letter, this is why
       category is called "letter" here.

       .. _genindex: https://www.sphinx-doc.org/en/master/genindex.html

    """

    #: Possible value of :py:attr:`~sphinx.domains.IndexEntry.subtype`.
    #:
    #: - 0: normal entry
    #: - 1: entry with sub-entries
    #: - 2: sub-entry
    type IndexEntrySubtype = Literal[0, 1, 2]

    category: str  # main category
    entry: str | None = None  # sub category or just for sorting
    subentry: str | None = None  # just for sorting

    @property
    def index_entry_subtype(self) -> IndexEntrySubtype:
        assert not (self.entry is None and self.subentry is not None)
        if self.subentry is not None:
            return 2
        if self.entry is not None:
            return 1
        return 0

    @property
    def leaf(self) -> str:
        if self.subentry is not None:
            return self.subentry
        if self.entry is not None:
            return self.entry
        return self.category

    def as_category(self) -> 'Classif':
        return Classif(category=self.category)

    def as_entry(self) -> 'Classif | None':
        if self.subentry is None:  # TODO:
            return None
        return Classif(category=self.category, entry=self.entry)

    @property
    def _sort_key(self) -> tuple[str, str | None, str | None]:
        return (self.category, self.entry, self.subentry)

    def __hash__(self):
        return hash(self._sort_key)


class Classifier(object):
    name = ''

    @abstractmethod
    def classify(self, objref: Value) -> list[Classif]:
        raise NotImplementedError

    _T = TypeVar('_T')

    @abstractmethod
    def sort(self, data: Iterable[_T], key: Callable[[_T], Classif]) -> list[_T]:
        # TODO: should have same kind
        raise NotImplementedError


class PlainClassifier(Classifier):
    name = ''

    def classify(self, objref: Value) -> list[Classif]:
        entries = []
        for v in objref.as_list():
            entries.append(Classif(category=v))
        return entries

    def sort(
        self, data: Iterable[Classifier._T], key: Callable[[Classifier._T], Classif]
    ) -> list[Classifier._T]:
        # TODO: should have same kind
        return sorted(data, key=lambda x: key(x)._sort_key)


class DateClassifier(Classifier):
    name = 'by-date'

    def __init__(self, datefmts: list[str]):
        """datefmt is format used by time.strptime()."""
        self.datefmts = datefmts

    def classify(self, objref: Value) -> list[Classif]:
        entries = []
        for v in objref.as_list():
            for datefmt in self.datefmts:
                try:
                    t = strptime(v, datefmt)
                except ValueError:
                    continue  # try next datefmt
                entries.append(
                    Classif(
                        category=str(t.tm_year),
                        entry=str(t.tm_mon),
                        subentry=str(t.tm_mday),
                    )
                )
        return entries

    def sort(
        self, data: Iterable[Classifier._T], key: Callable[[Classifier._T], Classif]
    ) -> list[Classifier._T]:
        # From newest to oldest.
        return sorted(data, key=lambda x: key(x)._sort_key, reverse=True)


@dataclasses.dataclass(frozen=True)
class Object(object):
    objtype: str
    name: str | None
    attrs: dict[str, str]
    content: str | None

    def hexdigest(self) -> str:
        return hashlib.sha1(pickle.dumps(self)).hexdigest()[:7]


@dataclasses.dataclass
class Field(object):
    """
    Describes value constraint of field of Object.

    The value of field can be single or mulitple string.

    :param form: The form of value.
    :param uniq: Whether the field is unique.
        If true, the value of field must be unique within the scope of objects
        with same type. And it will be used as base string of object
        identifier.

        Only one unique field is allowed in one object type.

        .. note::

            Duplicated value causes a warning when building documentation,
            and the corresponding object cannot be referenced correctly.
    :param ref: Whether the field is referenceable.
        If ture, object can be referenced by field value.
        See :ref:`roles` for more details.

    :param required: Whether the field is required.
        If ture, :py:exc:`ObjectError` will be raised when building documentation
        if the value is no given.
    """

    class Forms:
        PLAIN = Single()
        STRIPPED = Single(strip=True)
        WORDS = List(sep=' ', strip=True)
        LINES = List(sep='\n')
        STRIPPED_LINES = List(sep='\n', strip=True)

    uniq: bool = False
    ref: bool = False
    required: bool = False
    form: Form = Forms.PLAIN
    classifiers: list[Classifier] = dataclasses.field(
        default_factory=lambda: [PlainClassifier()]
    )

    def value_of(self, rawval: str | None) -> Value:
        if rawval is None:
            assert not self.required
            return Value(None)
        return self.form.extract(rawval)


class Schema(object):
    """
    Schema is used to describe objects, and be able to generate corresponding
    directive, role and index for describing, referencing, and indexing specific
    object.
    """

    #: Template variable name of object type
    TYPE_KEY = 'type'
    #: Template variable name of object name
    NAME_KEY = 'name'
    #: Template variable name of object content
    CONTENT_KEY = 'content'
    #: Template variable name of object title
    TITLE_KEY = 'title'

    # Object type
    objtype: str

    # Object fields, use :py:meth:`Schema.fields`
    name: Field | None
    attrs: dict[str, Field]
    content: Field | None

    description_template: str
    reference_template: str
    missing_reference_template: str
    ambiguous_reference_template: str

    def __init__(
        self,
        objtype: str,
        name: Field | None = Field(uniq=True, ref=True),
        attrs: dict[str, Field] = {},
        content: Field | None = Field(),
        description_template: str = '{{ content }}',
        reference_template: str = '{{ title }}',
        missing_reference_template: str = '{{ title }} (missing reference)',
        ambiguous_reference_template: str = '{{ title }} (disambiguation)',
    ) -> None:
        """Create a Schema instance.

        :param objtype: The unique type name of object, it will be used as
            basename of corresponding :ref:`directives`, :ref:`roles` and
            :ref:`indices`
        :param name: Constraints of optional object name
        :param attrs: Constraints of object attributes
        :param content: Constraints of object content
        :param description_template: See :ref:`description-template`
        :param reference_template: See :ref:`reference-template`
        :param missing_reference_template: See :ref:`reference-template`
        :param ambiguous_reference_template: See :ref:`reference-template`
        """

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
        all_fields = [self.name, self.content] + list(self.attrs.values())
        for field in all_fields:
            if field is None:
                continue
            if has_unique and field.uniq:
                raise SchemaError('only one unique field is allowed in schema')
            else:
                has_unique = field.uniq

    def fields(self, all=True) -> list[tuple[str, Field]]:
        """Return all fields of schema, including name and content.

        .. note::

           Return a tuple list rather than dict to prevent overwrite of fields
           with the same name.
        """

        fields = list(self.attrs.items())
        if all and self.content is not None:
            fields.insert(0, (self.CONTENT_KEY, self.content))
        if all and self.name is not None:
            fields.insert(0, (self.NAME_KEY, self.name))
        return fields

    def object(
        self, name: str | None, attrs: dict[str, str], content: str | None
    ) -> Object:
        """Generate a object"""
        obj = Object(objtype=self.objtype, name=name, attrs=attrs, content=content)
        for name, field, val in self.fields_of(obj):
            if field.required and val is None:
                raise ObjectError(f'field {name} is required')
        return obj

    def fields_of(
        self, obj: Object
    ) -> Iterator[tuple[str, Field, None | str | list[str]]]:
        """
        Helper method for returning all fields of object and its raw values.
        -> Iterator[field_name, field_instance, field_value],
        while the field_value is string_value|string_list_value.
        """
        if self.name:
            yield (
                self.NAME_KEY,
                self.name,
                self.name.value_of(obj.name).value,
            )
        for name, field in self.attrs.items():
            yield (
                name,
                field,
                field.value_of(obj.attrs.get(name)).value,
            )
        if self.content:
            yield (
                self.CONTENT_KEY,
                self.content,
                self.content.value_of(obj.content).value,
            )

    def name_of(self, obj: Object) -> None | str | list[str]:
        assert obj
        if self.name is None:
            return None
        return self.name.value_of(obj.name).value

    def attrs_of(self, obj: Object) -> dict[str, None | str | list[str]]:
        assert obj
        return {k: f.value_of(obj.attrs.get(k)).value for k, f in self.attrs.items()}

    def content_of(self, obj: Object) -> None | str | list[str]:
        assert obj
        if self.content is None:
            return None
        return self.content.value_of(obj.content).value

    def identifier_of(self, obj: Object) -> tuple[str | None, str]:
        """
        Return unique identifier of object.
        If there is not any unique field, return (None, obj.hexdigest()) instead.
        """
        assert obj
        for name, field, val in self.fields_of(obj):
            if not field.uniq:
                continue
            if val is None:
                break
            elif isinstance(val, str):
                return name, val
            elif isinstance(val, list) and len(val) > 0:
                return name, val[0]
        return None, obj.hexdigest()

    def title_of(self, obj: Object) -> str | None:
        """Return title (display name) of object."""
        assert obj
        if self.name is None:
            return None
        name = self.name.value_of(obj.name)
        if name is None:
            return None
        name = name.value
        if isinstance(name, str):
            return name
        elif isinstance(name, list) and len(name) > 0:
            return name[0]
        else:
            return None

    def references_of(self, obj: Object) -> set[tuple[str, str]]:
        """Return all references (referenceable fields) of object"""
        assert obj
        refs = []
        for name, field, val in self.fields_of(obj):
            if not field.ref:
                continue
            if val is None:
                continue
            elif isinstance(val, str):
                refs.append((name, val))
            elif isinstance(val, list):
                refs += [(name, x.strip()) for x in val if x.strip() != '']
        return set(refs)

    def _context_without_object(self) -> dict[str, str | list[str]]:
        return {
            self.TYPE_KEY: self.objtype,
        }

    def _context_of(self, obj: Object) -> dict[str, str | list[str]]:
        context = self._context_without_object()

        def set_if_not_none(key, val) -> None:
            if val is not None:
                context[key] = val

        set_if_not_none(self.NAME_KEY, self.name_of(obj))
        set_if_not_none(self.TITLE_KEY, self.title_of(obj))
        set_if_not_none(self.CONTENT_KEY, self.content_of(obj))
        for key, val in self.attrs_of(obj).items():
            set_if_not_none(key, val)

        return context

    def render_description(self, obj: Object) -> list[str]:
        assert obj
        tmpl = TemplateEnvironment().from_string(self.description_template)
        description = tmpl.render(self._context_of(obj))
        logger.debug(
            '[any] render description template %s: %s'
            % (self.description_template, description)
        )
        return description.split('\n')

    def render_reference(self, obj: Object) -> str:
        assert obj
        tmpl = TemplateEnvironment().from_string(self.reference_template)
        reference = tmpl.render(self._context_of(obj))
        logger.debug(
            '[any] render references template %s: %s',
            self.reference_template,
            reference,
        )
        return reference

    def _render_reference_without_object(
        self, explicit_title: str, reference_template: str
    ) -> str:
        context = self._context_without_object()
        context[self.TITLE_KEY] = explicit_title
        tmpl = TemplateEnvironment().from_string(reference_template)
        reference = tmpl.render(context)
        logger.debug(
            '[any] render references template without object %s: %s',
            reference_template,
            reference,
        )
        return reference

    def render_missing_reference(self, explicit_title: str) -> str:
        logger.debug('[any] render missing references template %s', explicit_title)
        return self._render_reference_without_object(
            explicit_title, self.missing_reference_template
        )

    def render_ambiguous_reference(self, explicit_title: str) -> str:
        logger.debug('[any] render ambiguous references template %s', explicit_title)
        return self._render_reference_without_object(
            explicit_title, self.ambiguous_reference_template
        )

    def __eq__(self, other: Any) -> bool:
        """
        Schema is dynamically created and used in sphinx configuration,
        in order to prevent config changed (lead to sphinx environment rebuild),
        we regard schemas with same attributes are equal.
        """
        if not isinstance(other, Schema):
            return False
        return pickle.dumps(self) == pickle.dumps(other)

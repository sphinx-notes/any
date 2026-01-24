"""
sphinxnotes.obj.obj
~~~~~~~~~~~~~~~~~~~

Basic object and related types definitons.

:copyright: Copyright 2026 Shengyu Zhang
:license: BSD, see LICENSE for details.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, TypeVar
from abc import ABC, abstractmethod
import hashlib
import pickle
from dataclasses import dataclass

from sphinxnotes.data import (
    REGISTRY,
    ParsedData,
    PlainValue,
    Value,
    ValueWrapper,
    Template,
    Phase,
    Schema,
)

if TYPE_CHECKING:
    from typing import Self, Literal, Iterable, Callable

# ====================
# Object related types
# ====================

# A better name in this context.
type Object = ParsedData


@dataclass
class RefType(object):
    """Reference type, object can be referenced:

    - by type *objtype*
    - by field *objtype*.*field*
    - by field index *objtype*.*field*+by-*index*
    """

    #: Object type, one of :member:`ObjDomain.object_types`.
    objtype: str
    #: Name of field, see :attr:`Schema.Field.name`.
    field: str | None = None
    #: Name of indexer, see :attr:`Indexer.name`.
    indexer: str | None = None

    @classmethod
    def parse(cls, reftype: str) -> Self:
        """
        Format: <objtype>[.<field>[+<action>]].
        Possible action: "by-<indexer>".
        """

        if '+' in reftype:
            reftype, action = reftype.split('+', 1)
            if action.startswith('by-'):
                index = action[3:]
            else:
                raise ValueError(f'unknown action {action} in RefType {reftype}')
        else:
            index = None

        if '.' in reftype:
            objtype, field = reftype.split('.', 1)
        else:
            objtype, field = reftype, None

        return cls(objtype, field, index)

    def __str__(self) -> str:
        """Used as role name and index name."""
        s = self.objtype
        if self.field:
            s += '.' + self.field
        if self.indexer:
            s += '+' + 'by-' + self.indexer
        return s


class Templates:
    """A set of templates that used for rendering object itself,
    cross-references, and etc."""

    """Templates for rendering object"""
    content: Template
    header: Template | None

    # embed: Templates

    """Templates for rendering corss references."""
    ref: Template
    ref_by: dict[str, Template]

    """Templates for rendering index entry."""
    # ...

    # TODO: more...?

    def __init__(
        self,
        content: str,
        header: str | None,
        ref: str,  # | None
        ref_by: dict[str, str] = {},
        debug: bool = False,
    ):
        self.content = Template(content, Phase.Parsing, debug)
        self.header = Template(header, Phase.Parsing, debug) if header else None
        self.ref = Template(ref, Phase.PostTranform, debug)
        self.ref_by = {
            f: Template(t, Phase.PostTranform, debug) for f, t in ref_by.items()
        }

    def get_ref_by(self, reftype: RefType) -> Template:
        if reftype.field is not None:
            if t := self.ref_by.get(reftype.field):
                return t
        return self.ref


# ============================
# Basic types for object index
# ============================


@dataclass
class Category:
    """
    Classification and sorting of an object, and generating
    py:cls:`sphinx.domain.IndexEntry`.

    :py:meth:`sphinx.domain.Index.generate` returns ``(content, collapse)``,
    and type of  ``contents`` is a list of ``(letter, IndexEntry list)``.
    letter is category of index entries, and some of index entries may be followed
    by sub-entries (distinguish by :py:attr:`~sphinx.domains.IndexEntry.subtype`).
    So Sphinx's index can represent up to 2 levels of indexing:

    :single index: letter -> normal entry
    :dual index:   letter -> entry with sub-entries -> sub-entry

    Category can be used to generating all of 3 kinds of IndexEntry:

    :normal entry:            Category(main=X)
    :entry with sub-entries:  Category(main=X, sub=Y, extra=None)
    :sub-entry:               Category(main=X, sub=Y, extra=Z)

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

    #: Main category of entry.
    main: str
    # Possible sub category of entry.
    sub: str | None = None
    #: Value of :py:attr:`sphinx.domains.IndexEntry.extra`.
    extra: str | None = None

    def index_entry_subtype(self) -> IndexEntrySubtype:
        if self.sub is not None:
            return 2 if self.extra is not None else 1
        return 0

    def as_main(self) -> Category:
        return Category(main=self.main)

    def as_sub(self) -> Category | None:
        if self.sub is None:
            return None
        return Category(main=self.main, sub=self.sub)

    @property
    def _sort_key(self) -> tuple[str, str | None, str | None]:
        return (self.main, self.sub, self.extra)

    def __hash__(self):
        return hash(self._sort_key)


class Indexer(ABC):
    name: str

    _T = TypeVar('_T')

    """Methods to be implemented."""

    @abstractmethod
    def classify(self, objref: Value) -> list[Category]: ...

    @abstractmethod
    def anchor(self, refval: str) -> str: ...

    """Methods with default implemention."""

    def sort(self, data: Iterable[_T], key: Callable[[_T], Category]) -> list[_T]:
        return sorted(data, key=lambda x: key(x)._sort_key)


# =============================
# Support for extra field flags
# =============================


def _register_field_flags() -> None:
    # NOTE: Add a "uniq" flag to data.Field.
    # user can acccess flag by accessing ``data.Field.uniq``.
    # The same applies below.
    REGISTRY.data.add_flag('uniq', aliases=['unique'])
    REGISTRY.data.add_flag('ref', aliases=['refer', 'referable', 'referenceable'])

    REGISTRY.data.add_by_option('index', str, store='append', aliases=['idx'])


def validate_schema(schema: Schema) -> None:
    has_uniq = False
    for _, field in schema.fields():
        if field is None:
            continue
        if has_uniq and field.uniq:
            raise ValueError('only one unique field is allowed in schema')
        else:
            has_uniq = field.uniq


def get_object_uniq_ids(schema: Schema, obj: Object) -> list[PlainValue]:
    """
    Return unique identifier of object.
    If there is not any unique field, return (None, sha1) instead.
    """
    for _, field, val in schema.items(obj):
        if not field.uniq:
            continue
        return ValueWrapper(val).as_list()

    # Fallback to SHA1 when there is not unique field.
    sha1 = hashlib.sha1(pickle.dumps(obj)).hexdigest()[:7]
    return [sha1]


def get_object_refs(schema: Schema, obj: Object) -> set[tuple[str, PlainValue]]:
    """Return all references (referenceable fields) of object"""
    assert obj
    refs = []
    for name, field, val in schema.items(obj):
        if not field.ref:
            continue
        refs += [(name, x) for x in ValueWrapper(val).as_list()]
    return set(refs)


def get_object_title(obj: Object) -> str | None:
    return ValueWrapper(obj.name).as_str()


_register_field_flags()

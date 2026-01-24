"""
sphinxnotes.any.indexers
~~~~~~~~~~~~~~~~~~~~~~~~

:cls:`objects.Indexer` implementations.

:copyright: Copyright 2024 Shengyu Zhang
:license: BSD, see LICENSE for details.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, override

from sphinxnotes.data import Value, ValueWrapper

from .obj import Category, Indexer
from .datetime import PartialDate

if TYPE_CHECKING:
    from typing import Literal, Iterable, Callable


class LiteralIndexer(Indexer):
    name = 'literal'

    @override
    def classify(self, objref: Value) -> list[Category]:
        entries = []
        for v in ValueWrapper(objref).as_str_list():
            entries.append(Category(main=v))
        return entries

    @override
    def anchor(self, refval: str) -> str:
        # https://github.com/sphinx-doc/sphinx/blob/df3d94ffdad09cc2592caccd179004e31aa63227/sphinx/themes/basic/domainindex.html#L28
        return 'cap-' + refval


class PathIndexer(Indexer):
    name = 'path'

    def __init__(self, sep: str, maxsplit: Literal[1, 2]):
        self.sep = sep
        self.maxsplit = maxsplit

    @override
    def classify(self, objref: Value) -> list[Category]:
        entries = []
        for v in ValueWrapper(objref).as_str_list():
            comps = v.split(self.sep, maxsplit=self.maxsplit)
            category = Category(main=comps[0], extra=v)
            if self.maxsplit == 2:
                category.sub = comps[1] if len(comps) > 1 else None
            entries.append(category)
        return entries

    @override
    def anchor(self, refval: str) -> str:
        return 'cap-' + refval.split(self.sep, maxsplit=self.maxsplit)[0]


# I am Chinese :D
# So the date formats follow Chinese conventions.
# TODO: conf
INPUTFMTS = ['%Y-%m-%d', '%Y-%m', '%Y']
DISPFMTS_Y = '%Y 年'
DISPFMTS_M = '%m 月'
DISPFMTS_YM = '%Y 年 %m 月'
DISPFMTS_DW = '%d 日，%a'
ZEROTIME = PartialDate.from_str('0001', '%Y')


def _safe_strptime(datestr, fmt) -> PartialDate:
    if datestr is None or datestr == '':
        return ZEROTIME
    try:
        return PartialDate.from_str(datestr, fmt)
    except ValueError:
        return ZEROTIME


class YearIndexer(Indexer):
    name = 'year'

    def __init__(
        self,
        dispfmt_y: str = DISPFMTS_Y,
        dispfmt_m: str = DISPFMTS_M,
        dispfmt_dw: str = DISPFMTS_DW,
    ):
        """*xxxfmt* are date format used by time.strptime/strftime.

        .. seealso:: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes"""
        self.dispfmt_y = dispfmt_y
        self.dispfmt_m = dispfmt_m
        self.dispfmt_dw = dispfmt_dw

    @override
    def classify(self, objref: Value) -> list[Category]:
        entries = []
        for v in ValueWrapper(objref).as_list():
            assert isinstance(v, PartialDate)

            if v.no_month:
                entry = Category(main=v.strftime(self.dispfmt_y))
            if v.no_day:
                entry = Category(
                    main=v.strftime(self.dispfmt_y),
                    sub=v.strftime(self.dispfmt_m),
                    extra='',  # left it empty, or sub-type will not take effect
                )
            else:
                entry = Category(
                    main=v.strftime(self.dispfmt_y),
                    sub=v.strftime(self.dispfmt_m),
                    extra=v.strftime(self.dispfmt_dw),
                )
            entries.append(entry)

        return entries

    @override
    def sort(
        self, data: Iterable[Indexer._T], key: Callable[[Indexer._T], Category]
    ) -> list[Indexer._T]:
        def sort_by_time(x: Category):
            t1 = _safe_strptime(x.main, self.dispfmt_y)
            t2 = _safe_strptime(x.sub, self.dispfmt_m)
            t3 = _safe_strptime(x.extra, self.dispfmt_dw)
            return (t1, t2, t3)

        return sorted(data, key=lambda x: sort_by_time(key(x)), reverse=True)

    @override
    def anchor(self, refval: str) -> str:
        if refval == '':
            return ''
        date = PartialDate.from_str(refval)
        anchor = date.strftime(self.dispfmt_y)
        return f'cap-{anchor}'


class MonthIndexer(Indexer):
    name = 'month'

    def __init__(
        self,
        dispfmt_ym: str = DISPFMTS_YM,
        dispfmt_dw: str = DISPFMTS_DW,
    ):
        self.dispfmt_ym = dispfmt_ym
        self.dispfmt_dw = dispfmt_dw

    @override
    def classify(self, objref: Value) -> list[Category]:
        entries = []
        for v in ValueWrapper(objref).as_list():
            assert isinstance(v, PartialDate)

            if v.no_day:
                entry = Category(main=v.strftime(self.dispfmt_ym))
            else:
                entry = Category(
                    main=v.strftime(self.dispfmt_ym), extra=v.strftime(self.dispfmt_dw)
                )
            entries.append(entry)
        return entries

    def sort(
        self, data: Iterable[Indexer._T], key: Callable[[Indexer._T], Category]
    ) -> list[Indexer._T]:
        def sort_by_time(x: Category):
            t1 = _safe_strptime(x.main, self.dispfmt_ym)
            t2 = _safe_strptime(x.extra, self.dispfmt_dw)
            return (t1, t2)

        return sorted(data, key=lambda x: sort_by_time(key(x)), reverse=True)

    @override
    def anchor(self, refval: str) -> str:
        date = PartialDate.from_str(refval)
        anchor = date.strftime(self.dispfmt_ym)
        return f'cap-{anchor}'

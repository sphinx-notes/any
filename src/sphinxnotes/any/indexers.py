"""
sphinxnotes.any.indexers
~~~~~~~~~~~~~~~~~~~~~~~~

:cls:`objects.Indexer` implementations.

:copyright: Copyright 2024 Shengyu Zhang
:license: BSD, see LICENSE for details.
"""

from typing import TYPE_CHECKING, Literal, Iterable, Callable, override
from time import strptime, strftime
from datetime import datetime, date, time

from .obj import Category, Indexer

from sphinxnotes.data import Value, ValueWrapper

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
ZEROTIME = strptime('0001', '%Y')


def _safe_strptime(datestr, fmt):
    if datestr is None or datestr == '':
        return ZEROTIME
    try:
        return strptime(datestr, fmt)
    except ValueError:
        return ZEROTIME


class YearIndexer(Indexer):
    name = 'year'

    @override
    def classify(self, objref: Value) -> list[Category]:
        entries = []
        for v in ValueWrapper(objref).as_list():
            assert isinstance(v, (datetime, date))

            for datefmt in self.inputfmts:
                try:
                    t = strptime(v, datefmt)
                except ValueError:
                    continue  # try next datefmt

                if all(x not in datefmt for x in ['%m', '%b', '%B']):  # missing month
                    entry = Category(main=strftime(self.dispfmt_y, t))
                elif all(x not in datefmt for x in ['%d', '%j']):  # missing day
                    entry = Category(
                        main=strftime(self.dispfmt_y, t),
                        sub=strftime(self.dispfmt_m, t),
                        extra='',  # TODO: leave it empty, or sub-type will not take effect
                    )
                else:
                    entry = Category(
                        main=strftime(self.dispfmt_y, t),
                        sub=strftime(self.dispfmt_m, t),
                        extra=strftime(self.dispfmt_dw, t),
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
        for datefmt in self.inputfmts:
            try:
                t = strptime(refval, datefmt)
            except ValueError:
                continue  # try next datefmt
            anchor = strftime(self.dispfmt_y, t)
            return f'cap-{anchor}'
        return ''


class MonthIndexer(Indexer):
    name = 'month'

    def __init__(
        self,
        inputfmts: list[str] = INPUTFMTS,
        dispfmt_ym: str = DISPFMTS_YM,
        dispfmt_dw: str = DISPFMTS_DW,
    ):
        self.inputfmts = inputfmts
        self.dispfmt_ym = dispfmt_ym
        self.dispfmt_dw = dispfmt_dw

    @override
    def classify(self, objref: Value) -> list[Category]:
        entries = []
        for v in ValueWrapper(objref).as_str_list():
            for datefmt in self.inputfmts:
                try:
                    t = strptime(v, datefmt)
                except ValueError:
                    continue  # try next datefmt

                if all(x not in datefmt for x in ['%d', '%j']):  # missing day
                    entry = Category(main=strftime(self.dispfmt_ym, t))
                else:
                    entry = Category(
                        main=strftime(self.dispfmt_ym, t),
                        extra=strftime(self.dispfmt_dw, t),
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
        for datefmt in self.inputfmts:
            try:
                t = strptime(refval, datefmt)
            except ValueError:
                continue  # try next datefmt
            anchor = strftime(self.dispfmt_ym, t)
            return f'cap-{anchor}'
        return ''

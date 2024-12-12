"""
sphinxnotes.any.indexers
~~~~~~~~~~~~~~~~~~~~~~~~

:cls:`objects.Indexer` implementations.

:copyright: Copyright 2024 Shengyu Zhang
:license: BSD, see LICENSE for details.
"""

from typing import Iterable, Literal, Callable
from time import strptime, strftime

from .objects import Indexer, Category, Value


class LiteralIndexer(Indexer):
    name = 'literal'

    def classify(self, objref: Value) -> list[Category]:
        entries = []
        for v in objref.as_list():
            entries.append(Category(main=v))
        return entries

    def anchor(self, refval: str) -> str:
        # https://github.com/sphinx-doc/sphinx/blob/df3d94ffdad09cc2592caccd179004e31aa63227/sphinx/themes/basic/domainindex.html#L28
        return 'cap-' + refval


DEFAULT_INDEXER = LiteralIndexer()


class PathIndexer(Indexer):
    name = 'path'

    def __init__(self, sep: str, maxsplit: Literal[1, 2]):
        self.sep = sep
        self.maxsplit = maxsplit

    def classify(self, objref: Value) -> list[Category]:
        entries = []
        for v in objref.as_list():
            comps = v.split(self.sep, maxsplit=self.maxsplit)
            category = Category(main=comps[0], extra=v)
            if self.maxsplit == 2:
                category.sub = v[1] if len(comps) > 1 else None
            entries.append(category)
        return entries

    def anchor(self, refval: str) -> str:
        return refval.split(self.sep, maxsplit=self.maxsplit)[0]


# I am Chinese :D
# So the date formats follow Chinese conventions.
# TODO: conf
INPUTFMTS = ['%Y-%m-%d', '%Y-%m', '%Y']
DISPFMTS_Y = '%Y 年'
DISPFMTS_M = '%m 月'
DISPFMTS_YM = '%Y 年 %m 月'
DISPFMTS_MD = '%m 月 %d 日，%a'


class YearIndexer(Indexer):
    name = 'year'

    def __init__(
        self,
        inputfmts: list[str] = INPUTFMTS,
        dispfmt_y: str = DISPFMTS_Y,
        dispfmt_m: str = DISPFMTS_M,
        dispfmt_md: str = DISPFMTS_MD,
    ):
        """*xxxfmt* are date format used by time.strptime/strftime.

        .. seealso:: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes"""
        self.inputfmts = inputfmts
        self.dispfmt_y = dispfmt_y
        self.dispfmt_m = dispfmt_m
        self.dispfmt_md = dispfmt_md

    def classify(self, objref: Value) -> list[Category]:
        entries = []
        for v in objref.as_list():
            for datefmt in self.inputfmts:
                try:
                    t = strptime(v, datefmt)
                except ValueError:
                    continue  # try next datefmt
                entries.append(
                    Category(
                        main=strftime(self.dispfmt_y, t),
                        sub=strftime(self.dispfmt_m, t),
                        extra=strftime(self.dispfmt_md, t),
                    )
                )
        return entries

    def sort(
        self, data: Iterable[Indexer._T], key: Callable[[Indexer._T], Category]
    ) -> list[Indexer._T]:
        def sort_by_time(x: Category):
            t1 = strptime(x.main, self.dispfmt_y)
            t2 = strptime(x.sub, self.dispfmt_m) if x.sub else None
            t3 = strptime(x.extra, self.dispfmt_md) if x.extra else None
            return (t1, t2, t3)

        return sorted(data, key=lambda x: sort_by_time(key(x)), reverse=True)

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
        dispfmt_md: str = DISPFMTS_MD,
    ):
        self.inputfmts = inputfmts
        self.dispfmt_ym = dispfmt_ym
        self.dispfmt_md = dispfmt_md

    def classify(self, objref: Value) -> list[Category]:
        entries = []
        for v in objref.as_list():
            for datefmt in self.inputfmts:
                try:
                    t = strptime(v, datefmt)
                except ValueError:
                    continue  # try next datefmt
                entries.append(
                    Category(
                        main=strftime(self.dispfmt_ym, t),
                        extra=strftime(self.dispfmt_md, t),
                    )
                )
        return entries

    def sort(
        self, data: Iterable[Indexer._T], key: Callable[[Indexer._T], Category]
    ) -> list[Indexer._T]:
        def sort_by_time(x: Category):
            t1 = strptime(x.main, self.dispfmt_ym)
            t2 = strptime(x.sub, self.dispfmt_md) if x.sub else None
            return (t1, t2)

        return sorted(data, key=lambda x: sort_by_time(key(x)), reverse=True)

    def anchor(self, refval: str) -> str:
        for datefmt in self.inputfmts:
            try:
                t = strptime(refval, datefmt)
            except ValueError:
                continue  # try next datefmt
            anchor = strftime(self.dispfmt_ym, t)
            return f'cap-{anchor}'
        return ''

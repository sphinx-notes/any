"""
sphinxnotes.data.datetime
~~~~~~~~~~~~~~~~~~~~~~~~~

Datetime value support. Mostly for indexer.{Year,Month}Indexer.

:copyright: Copyright 2025~2026 by the Shengyu Zhang.
:license: BSD, see LICENSE for details.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, override
from datetime import date, datetime

from sphinxnotes.data import REGISTRY

if TYPE_CHECKING:
    from typing import Self
    from sphinx.application import Sphinx
    from sphinx.config import Config as Config

DATE_FMTS: list[str] = []


class PartialDate(date):
    """A date sub class that allow user to emit month and day."""

    no_month: bool
    no_day: bool

    @classmethod
    def from_date(cls, d: date, fmt: str) -> Self:
        month = d.month if any(x in fmt for x in ['%m', '%b', '%B']) else None
        day = d.day if any(x in fmt for x in ['%d', '%j']) else None
        return cls(d.year, month, day)

    @classmethod
    def from_str(cls, rawval: str, fmt: str | None = None) -> Self:
        lasterr = None
        fmts = [fmt] if fmt else DATE_FMTS
        for f in fmts:
            try:
                dt = datetime.strptime(rawval, f)
            except ValueError as e:
                lasterr = e
                continue  # try next
            return cls.from_date(dt, f)

        raise ValueError(f'parse date from formats: {fmts}, last error: {lasterr}')

    """Methods to make pickle work correctly."""

    @override
    def __new__(cls, year: int, month: int | None = None, day: int | None = None):
        instance = super().__new__(cls, year, month or 1, day or 1)
        instance.no_month = month is None
        instance.no_day = day is None
        return instance

    @override
    def __reduce__(self):
        return (
            self.__class__,
            (
                self.year,
                None if self.no_month else self.month,
                None if self.no_day else self.day,
            ),
        )


def _config_inited(app: Sphinx, config: Config) -> None:
    DATE_FMTS.extend(config.obj_date_fmts)


def setup(app: Sphinx) -> None:
    app.add_config_value('obj_date_fmts', ['%Y-%m-%d', '%Y-%m', '%Y'], '', types=list)
    app.connect('config-inited', _config_inited)


REGISTRY.data.add_type('date', PartialDate, PartialDate.from_str, str)

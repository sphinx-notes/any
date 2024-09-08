"""
sphinxnotes.any.api
~~~~~~~~~~~~~~~~~~~

Public API for building configuration of extension.
(such as object schema, and so on).

:copyright: Copyright 2024 Shengyu Zhang
:license: BSD, see LICENSE for details.
"""

from .objects import Schema, Field
from .indexers import LiteralIndexer, PathIndexer, YearIndexer, MonthIndexer

# Object schema.
Schema = Schema
Field = Field

# Indexers.
LiteralIndexer = LiteralIndexer
PathIndexer = PathIndexer
YearIndexer = YearIndexer
MonthIndexer = MonthIndexer

# Indexer wrappers.
by_year = YearIndexer()
by_month = MonthIndexer()

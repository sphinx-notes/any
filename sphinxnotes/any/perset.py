"""
    sphinxnotes.any.preset
    ~~~~~~~~~~~~~~~~~~~~~~

    Preset sechemas for sphinxnotes.any.

    :copyright: Copyright 2021 Shengyu Zhang
    :license: BSD, see LICENSE for details.
"""

friend = {
    'type': 'friend',
    'fields': {
        'others': ['avatar', 'blog'],
    },
    'templates': {
        'reference': '@{{ title }}',
        'content': """
.. image:: {{ avatar }}
   :width: 120px
   :target: {{ blog }}
   :alt: {{ names[0] }}
   :align: left

:blog: {{ blog }}

{{ content | join('\n') }}"""
    }
}

book = {
    'type': 'book',
    'fields': {
        'id': 'isbn',
        'others': ['cover'],
    },
    'templates': {
        'reference': '《{{ title }}》',
        'content': """
:ISBN: {{ isbn }}

{{ content | join('\n') }}"""
    }
}

"""
    sphinxnotes.any.preset
    ~~~~~~~~~~~~~~~~~~~~~~

    Preset sechemas for sphinxnotes.any.

    :copyright: Copyright 2021 Shengyu Zhang
    :license: BSD, see LICENSE for details.
"""

from .domain import Schema, Field, dedent

friend = Schema('friend',
                {'avatar': Field(type=str), 'blog': Field(type=str)},
                description_template=dedent("""
                    .. image:: {{ avatar }}
                       :width: 120px
                       :target: {{ blog }}
                       :alt: {{ names[0] }}
                       :align: left

                    :blog: {{ blog }}

                    {{ content | join('\n') }}"""),
                reference_template='@{{ title }}')

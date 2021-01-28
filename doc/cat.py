schema = {
   'type': 'cat',
    'fields': {
        'id': 'catid',
        'others': ['owner', 'height', 'width', 'picture'],
    },
    'templates': {
        'reference': '🐈{{ title }}',
        'content': """
.. image:: {{ picture }}
   :align: left

:owner: {{ owner }}
:height: {{ height }}
:width: {{ width }}

{{ content | join('\n') }}"""
    }
}

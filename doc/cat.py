schema = {
   'type': 'cat',
    'fields': {
        'id': 'catid',
        'others': ['owner', 'height', 'width', 'picture'],
    },
    'templates': {
        'role': '🐈{{ title }}',
        'directive': """
.. image:: {{ picture }}
   :align: left

:owner: {{ owner }}
:height: {{ height }}
:width: {{ width }}

{{ content | join('\n') }}"""
    }
}

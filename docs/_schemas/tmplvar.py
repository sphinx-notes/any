from textwrap import dedent

tmplvar = {
    'schema': {
        'attrs': {
            'type': 'str',
        },
    },
    'templates': {
        'content': dedent("""
            :Type: ``{{ type }}``

            {{ content }}
        """),
        'ref': "{{ '{{' }}{{ name }}{{ '}}' }}",
    },
}

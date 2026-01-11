from textwrap import dedent

tmplvar = {
    'schema': {
        'name': 'str, uniq, ref',
        'attrs': {
            'type': 'str',
            'conf': 'str',
        },
    },
    'templates': {
        'obj': dedent("""
            {% if type %}:Type: ``{{ type }}`` {% endif %}

            {{ content }}

            {% if conf %}
            .. tip::

               Name of variables("{{ name }}") can be changed by setting
               :py:attr:`~any.Schema.{{ conf }}`
            {% endif %}"""),
        'ref': "{{ '{{' }}{{ title }}{{ '}}' }}",
    },
}

from textwrap import dedent
from any import Schema, Field

tmplvar = Schema(
    'tmplvar',
    name=Field(unique=True, referenceable=True),
    attrs={
        'type': Field(),
        'conf': Field(),
    },
    description_template=dedent("""
        {% if type %}:Type: ``{{ type }}`` {% endif %}

        {{ content }}

        {% if conf %}
        .. tip::

           Name of variables("{{ name }}") can be changed by setting
           :py:attr:`~any.Schema.{{ conf }}`
        {% endif %}"""),

    reference_template="{{ '{{' }}{{ title }}{{ '}}' }}",
    missing_reference_template="{{ '{{' }}{{ title }}{{ '}}' }}")

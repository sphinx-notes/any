
from textwrap import dedent
from any import Schema, Field

confval = Schema(
    'confval',
    name=Field(unique=True, referenceable=True),
    attrs={
        'type': Field(),
        'default': Field(),
    },
    description_template=dedent("""
        :Type: ``{{ type }}``
        :Default: ``{{ default}}``

        {{ content }}"""),
    reference_template='⚙️{{ title }}')

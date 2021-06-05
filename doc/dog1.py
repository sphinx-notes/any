from textwrap import dedent
from any import Schema, Field

dog = Schema('dog',
    attrs={
        'breed': Field(referenceable=True),
        'color': Field(referenceable=True, form=Field.Form.WORDS),
    },
    description_template=dedent("""
        :Breed: {{ breed }}
        :Colors: {{ colors }}"""),
    reference_template='🐕{{ title }}',
    ambiguous_reference_template='{{ title }}')

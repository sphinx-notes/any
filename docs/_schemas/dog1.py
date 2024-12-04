from textwrap import dedent
from any import Schema, Field

dog = Schema(
    'dog',
    attrs={
        'breed': Field(ref=True),
        'color': Field(ref=True, form=Field.Forms.WORDS),
    },
    description_template=dedent("""
        :Breed: {{ breed }}
        :Colors: {{ colors }}"""),
    reference_template='🐕{{ title }}',
    ambiguous_reference_template='{{ title }}',
)

from textwrap import dedent
from any.api import Schema, Field

dog = Schema(
    'dog',
    attrs={
        'breed': Field(ref=True),
        'color': Field(ref=True, form=Field.Forms.WORDS),
    },
    description_template=dedent("""
        :Breed: :any:dog.breed:`{{ breed }}`
        :Colors: {% for c in color %}:any:dog.color:`{{ c }}` {% endfor %}"""),
    reference_template='🐕{{ title }}',
    ambiguous_reference_template='{{ title }}',
)

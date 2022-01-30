from textwrap import dedent
from any import Schema, Field

dog = Schema('dog',
    attrs={
        'breed': Field(referenceable=True),
        'color': Field(referenceable=True, form=Field.Form.WORDS),
    },
    description_template=dedent("""
        :Breed: :any:dog.breed:`{{ breed }}`
        :Colors: {% for c in color %}:any:dog.color:`{{ c }}` {% endfor %}"""),
    reference_template='🐕{{ title }}',
    ambiguous_reference_template='{{ title }}')

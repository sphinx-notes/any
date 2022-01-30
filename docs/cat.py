from textwrap import dedent
from any import Schema, Field

cat = Schema('cat',
    name=Field(referenceable=True, form=Field.Form.LINES),
    attrs={
        'id': Field(unique=True, referenceable=True, required=True),
        'color': Field(referenceable=True),
        'picture': Field(),
    },
    description_template=dedent("""
        .. image:: {{ picture }}
           :align: left

        :Cat ID: {{ id }}
        :Color: {{ color }}

        {{ content }}"""),
    reference_template='🐈{{ title }}',
    missing_reference_template='😿{{ title }}',
    ambiguous_reference_template='😼{{ title }}')

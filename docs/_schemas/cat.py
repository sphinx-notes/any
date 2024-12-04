from textwrap import dedent
from any.api import Schema, Field

cat = Schema(
    'cat',
    name=Field(ref=True, form=Field.Forms.LINES),
    attrs={
        'id': Field(uniq=True, ref=True, required=True),
        'color': Field(ref=True),
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
    ambiguous_reference_template='😼{{ title }}',
)

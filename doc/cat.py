from textwrap import dedent
from any.schema import Schema, Field

cat = Schema(
    'cat',
    name=Field(referenceable=True, form=Field.Form.LINES),
    attrs={
        'id': Field(unique=True, referenceable=True, required=True),
        'owner': Field(),
        'height': Field(),
        'width': Field(),
        'picture': Field(),
    },
    description_template=dedent("""
        .. image:: {{ picture }}
           :align: left

        :owner: {{ owner }}
        :height: {{ height }}
        :width: {{ width }}

        {{ content }}"""),
    reference_template='🐈{{ title }}')

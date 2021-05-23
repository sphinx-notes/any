from textwrap import dedent
from any import Schema, Field

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
        {% if picture %}
        .. image:: {{ picture }}
           :align: left
        {% endif %}

        :owner: {{ owner }}
        :height: {{ height }}
        :width: {{ width }}

        {{ content }}"""),
    reference_template='🐈{{ title }}',
    missing_reference_template='😿{{ title }}',
    ambiguous_reference_template='😼{{ title }}')

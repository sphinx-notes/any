import os
import sys
import unittest
from textwrap import dedent

sys.path.insert(0, os.path.abspath('./sphinxnotes'))
from any import Schema, Field

class TestSchema(unittest.TestCase):
    def test_equal(self):
        self.assertEqual(Schema('cat'), Schema('cat'))
        self.assertEqual(self.new_schema(),
                         self.new_schema())

    def new_schema(self) -> Schema:
        return Schema('cat',
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
if __name__ == '__main__':
    unittest.main()

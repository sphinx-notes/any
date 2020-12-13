from docutils.utils import new_document
from docutils.parsers.rst import Parser
from docutils.frontend import OptionParser

input = '''
--------------------------------------------------------------------------------

.. image:: /_images/sphinx-notes.png
   :height: 120px
   :alt: alternate text
   :align: left

**SilverRainZ**

:sex: male
:org: Arch Linux CN

    You can adapt this file completely to your liking, but it should at least
    contain the root `toctree` directive.

--------------------------------------------------------------------------------
'''

parser = Parser()
document = new_document('source',
        settings = OptionParser(components=(Parser,)).get_default_values())
parser.parse(input, document)

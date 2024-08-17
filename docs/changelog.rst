.. This file is generated from sphinx-notes/cookiecutter.
   You need to consider modifying the TEMPLATE or modifying THIS FILE.

==========
Change Log
==========

.. hint:: You may want to learn about our `Release Strategy`__

   __ https://sphinx.silverrainz.me/release.html

.. Example:

   1.0
   ===

   .. version:: _
      :date: yyyy-mm-dd

   Change log here.

Version 2.x
===========

.. version:: 2.5
   :date: 2024-08-17

   - Add new Sphinx Domain classifier (:pull:`27`)
   - Strip rST markups in index description (:pull:`32`)
   - refactor: Combing and document srcdir, outdir, reldir
   - Fix referenceable field with multiple lines form (:issue:`34`)

.. version:: 2.4.0
   :date: 2023-08-26

   - Re-org project with sphinx-notes/template (:pull:`20`)
   - Require wand>0.6.11 to prevent crash on macOS (fa716d3)

.. version:: 2.3.1
   :date: 2022-06-26 

   - Fix crash when noting object with duplicate reference (:issue:`18`)

.. version:: 2.3
   :date: 2022-04-09 

   - Prevent crash when failed to get section title (72250de)
   - Return hexdigest rather than UUID as object ID (:pull:`7`)
   - Make all filters works again (:pull:`8`)
   - Correctly rendering title of cross reference (:pull:`12`)

.. version:: 2.2
   :date: 2021-08-18 

   - Use the Object ID as index name when no object title available

.. version:: 2.1
   :date: 2021-06-26

   - Report ambiguous object via debug log
   - Some doc fixes
   - Remove unused import

.. version:: 2.0
   :date: 2021-06-05

   - Update documentation, add some tips

.. version:: 2.0a3
   :date: 2021-06-03

   - Simplify index name (e4d9207)

.. version:: 2.0a2
   :date: 2021-05-23

   - Fix none object signture (6a5f75f)
   - Prevent sphinx config changed everytime (f7b316b)

.. version:: 2.0a1
   :date: 2021-05-23

   - Template variable must be non None (fb9678e)
   - Template will not apply on role with explicit title (5bdaad1)

.. version:: 2.0a0
   :date: 2021-05-22

   - Descibing schema with python object instead of dict
   - Support index
   - Refactor

Version 1.x
===========

.. version:: 1.1
   :date: 2021-02-28

   - Remove symbol link if exists

.. version:: 1.0
   :date: 2021-02-23

   - Move preset schemas to standalone package
   - Add custom filter support to template
   - Combine ``any_predefined_schemas`` and ``any_custom_schemas`` to ``any_schemas``

.. version:: 1.0b0
   :date: 2021-01-28

   - Fix the missing Jinja dependency
   - Use section title as object name when directive argument is omitted
   - Some code cleanups
   - Rename schema field "role" to "reference"
   - Rename schema field "directive" to "content"

.. version:: 1.0a1
   :date: 2020-12-20

   The alpha version is out, enjoy~

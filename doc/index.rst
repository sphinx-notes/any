===============
sphinxnotes.any
===============

------------------------------------
Sphinx Domain for Descibing Anything
------------------------------------

.. image:: https://img.shields.io/github/stars/sphinx-notes/any.svg?style=social&label=Star&maxAge=2592000
   :target: https://github.com/sphinx-notes/any

:version: |version|
:copyright: Copyright ©2021 by Shengyu Zhang.
:license: BSD, see LICENSE for details.

The extension provides a domain, allows user creates directive
and roles to descibe and reference arbitrary object by writing reStructuredText
template.

.. contents::
   :local:
   :backlinks: none

Installation
============

Download it from official Python Package Index:

.. code-block:: console

   $ pip install sphinxnotes-any

Add extension to :file:`conf.py` in your sphinx project:

.. code-block:: python

    extensions = [
              # …
              'sphinxnotes.any',
              # …
              ]

.. _Configuration:

Configuration
=============

The extension provides the following configuration:

:any_domain_name: (Type: ``str``, Default: `'any'`)
                  Name of the domain.

:any_schemas: (Type: ``List[sphinxnotes.any.Schema]``, Default: ``[]``)
              List of :ref:`schema <schema>` instances.

              For the way of writing schema definition, please refer to
              :ref:`writing-schema`.

Functionalities
===============

.. _writing-schema:

Writing Schema
--------------

.. _schema:

.. topic:: What is Schema?

    Before descibing any object, we need a "schema" to descibe "how to descibe the object".
    For extension user, "schema" is a python object that can specific in :file:`conf.py`.
    See :ref:`Configuration` for details.

An schema for descibing cat looks like this:

.. literalinclude:: ./cat.py
   :language: python

The aboved schema created a ``cat`` directive under "any" domain that
can descibe a cat.

.. note:: TODO

.. _writing-template:

Writing Template
----------------

We use Jinja2_ as our templating engine.

.. _Jinja2: https://jinja.palletsprojects.com/

Variables
~~~~~~~~~

For the usage of Jinja's variable, please refer to `Jinja2's Variables`_.

All fields defined in schema are available as variables in template.
Beside, there are some special variable:

``{{ title }}``
    Only available in "reference" template, represents the interpreted text.

``{{ names }}``
   Available in both "reference" and "description" template, represents the
   directive argument.

``{{ content }}``
   Available in both "reference" and "description" template, represents the
   directive content.

.. _Jinja2's Variables: <https://jinja.palletsprojects.com/en/2.11.x/templates/#variables

Filters
~~~~~~~

For the usage of Jinja's filter, please refer to `Jinja2's Filters`_.

All `Jinja2's Builtin Filters`_ are available.
In additional, we provide the following custom filters to enhance the template:

``copyfile(fn)``
    Copy a file in Sphinx srcdir to outdir, return the URI of file which relative
    to current documentation.

    The relative path to srcdir will be preserved, for example,
    ``{{ fn | copyfile }}`` while ``fn`` is :file:`_images/foo.jpg`,
    the file will copied to :file:`<OUTDIR>/_any/_images/foo.jpg`, and returns
    a POSIX path of ``fn`` which relative to current documentation.

``thumbnail(img, width, height)``
    Changes the size of an image to the given dimensions and removes any
    associated profiles, returns a a POSIX path of thumbnail which relative to
    current documentation.

    This filter always keep the origin aspect ratio of image.
    The width and height are optional, By default are 1280 and 720 respectively.

.. versionadded:: 1.0

.. _Jinja2's Filters: https://jinja.palletsprojects.com/en/2.11.x/templates/#filters>
.. _Jinja2's Builtin Filters: https://jinja.palletsprojects.com/en/2.11.x/templates/#builtin-filters

Using Newly Created Directive/Role
----------------------------------

Now we descibe a cat with the newly created directive:

.. literalinclude:: nyan-cat.txt
   :language: rst

It will be rendered as:

.. include:: nyan-cat.txt

The created directive accept only one argument, which indicates the name of object,
aliases can be added on another line after name, one alias per line.

If no argument given, or first one in argument (split by ``\n``) is ``_`` (underscore).
the object name will be indicated by title of current section.
This feature is useful when you want to use a whole section or documentation
to descibing object, for example:

.. literalinclude:: mimi.txt
   :language: rst

It will be rendered as:

.. include:: mimi.txt

.. versionadded:: 1.0

Use the ``any:cat`` role under "any" domain to reference Nyan Cat:

- Reference by name: ``:any:cat:`Nyan Cat``` -> :any:cat:`Nyan Cat`
- Reference by alias: ``:any:cat:`Nyan_Cat``` -> :any:cat:`Nyan_Cat`
- Reference by ID: ``:any:cat:`1``` -> :any:cat:`1`
- Explicit title is supported: ``:any:cat:`This cat <Nyan Cat>``` -> :any:cat:`This cat <Nyan Cat>`
- Reference a nonexistent cat: ``:any:cat:`gg``` -> :any:cat:`gg`

Beside, for all referenceable fieds, the corresponding roles is generated,
for example, try ``any:cat.name``:

- Exactly reference by name: ``:any:cat.name:`Nyan Cat``` -> :any:cat.name:`Nyan Cat`

Change Log
==========

2021-05-23 2.0a2
----------------

- Fix none object signture (6a5f75f)
- Prevent sphinx config changed everytime (f7b316b)

.. sectionauthor:: Shengyu Zhang
2021-05-23 2.0a1
----------------

- Template variable must be non None (fb9678e)
- Template will not apply on role with explicit title (5bdaad1)

.. sectionauthor:: Shengyu Zhang

2021-05-22 2.0a0
----------------

- Descibing schema with python object instead of dict
- Support index
- Refactor

2021-02-28 1.1
--------------

- Remove symbol link if exists

2021-02-23 1.0
--------------

- Move preset schemas to standalone package
- Add custom filter support to template
- Combine ``any_predefined_schemas`` and ``any_custom_schemas`` to ``any_schemas``

.. sectionauthor:: Shengyu Zhang

2021-01-28 1.0b0
----------------

- Fix the missing Jinja2 dependency
- Use section title as object name when directive argument is omitted
- Some code cleanups
- Rename schema field "role" to "reference"
- Rename schema field "directive" to "content"

.. sectionauthor:: Shengyu Zhang

2020-12-20 1.0a1
----------------

The alpha version is out, enjoy~

.. sectionauthor:: Shengyu Zhang

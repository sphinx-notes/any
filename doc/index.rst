===============
sphinxnotes.any
===============

------------------------------------
Sphinx Domain for Descibing Anything
------------------------------------

.. image:: https://img.shields.io/github/stars/sphinx-notes/any.svg?style=social&label=Star&maxAge=2592000
   :target: https://github.com/sphinx-notes/any

:version: |version|
:copyright: Copyright ©2020 by Shengyu Zhang.
:license: BSD, see LICENSE for details.

The extension provides a domain named "any", allows user creates directive
and roles to descibe and reference arbitrary object by writing restructedText
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

:any_schemas: (Type: ``List[Union[str,Dict]]``, Default: ``[]``)
              List of :ref:`preset-schemas` name or :ref:`schema <schema>` definition.

              For the way of writing schema definition, please refer to
              :ref:`writing-schema`.

              .. versionchanged:: 1.0 List element can be schema name or schema definition.

Functionalities
===============

.. _writing-schema:

Writing Schema
--------------

.. _schema:

.. topic:: What is Schema?

    Before descibing any object, we need a "schema" to descibe "how to descibe the object".
    For extension user, "schema" is a python ``dict`` that can specific in :file:`conf.py`.
    See :ref:`Configuration` for details.

An schema for descibing cat looks like this:

.. literalinclude:: ./cat.py
   :language: python

The aboved schema created a ``cat`` directive under "any" domain that
can descibe a cat.

The attributes of object can be indicates by directive options(a filed list).

**type**
    Type: ``str``, type of the object, it determines the name of the corresponding
    directive and role.
**fields**
    Type: ``Dict[str,Any]``, describe how many attributes the object has,
    it determines the options of corresponding directive,  and the **available
    variables when rendering template** (see below)

    **others**
        Type: ``List[str]``, list of name of non-special object attributes.

        The value will be one of options of created directive,
        and available as variable when rendering the template.

        For example, given ``['height']`` , the created directive
        will have ``:height:`` option with ``directives.unchanged`` flag,
        and the ``{{ height }}`` variable is available when rendering template.
    **id**
        Type: ``Optonal[str]``, name of the ID field, the value of ID of
        should be unique among whole documentation, when the object name is
        duplicated, user can still reference the correct object by ID.

        Same to ``others``, but the created directive option has flag
        ``directives.unchanged_required``.

        .. versionchanged:: 1.0b0

           If the value is empty string(``""``), use the default value "id".


**templates**
    Type: ``Dict[str,Any]``, contains templates that descibe how object
    will be show. Please refer to :ref:`writing-template` for more details.

    **reference**

        Template for rendering role's interpreted text.

        .. versionchanged:: 1.0b0 Renamed from "role" to "reference"

    **content**

        Template for rendering directive's content.

        .. versionchanged:: 1.0b0 Renamed from "directive" to "content"


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
    Type: ``str``, Only available in "reference" template,
    represents the origin interpreted text.

``{{ names }}``
   Type: ``List[str]``, Available in both "reference" and "content" template,
   represents the the only one directive argument after being ``split('\n')``.
   So note that it is **array of string** but not string.

   User can reference object name by ``{{ name[0] }}``.

``{{ content }}``
   Type: ``List[str]``, Available in both "reference" and "content" template,
   represents the origin directive content after being ``split('\n')``.
   So note that it is **array of string** but not string.

   If you want content to be parsed by Sphinx, you should use
   ``{{ content | join('\n') }}``.

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

.. note::

   This feature is useful when you want to use a whole section or documentation
   to descibing object, for example:

   .. code-block:: rst

      ========
      Nyan Dog
      ========

      .. any:cat::
         :catid: 2

      Blahblah...

.. versionadded:: 1.0


Use the ``cat`` role under "any" domain to reference Nyan Cat:

- Reference by name: ``:any:cat:`Nyan Cat``` -> :any:cat:`Nyan Cat`
- Reference by alias: ``:any:cat:`Nyan_Cat``` -> :any:cat:`Nyan_Cat`
- Reference by ID: ``:any:cat:`1``` -> :any:cat:`1`
- Explicit title is supported: ``:any:cat:`This cat <Nyan Cat>``` -> :any:cat:`This cat <Nyan Cat>`

.. _preset-schemas:

Preset Schemas
--------------

The extension provides some predefeined schemas for testing purpose and for
light users:

friend
    The "friend" schema is used to descibe your friend, provides ``friend``
    directive and ``friend`` role that helps you to contstruct your friend links.
book
    The "book" schema is used to note your book have read.

.. note:: TO BE COMPLETED.

Change Log
==========

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

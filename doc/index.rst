====================================
Sphinx Domain for Descibing Anything
====================================

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

:any_predefined_schemas: (Type: ``List[str]``, Default: ``['friend', 'book']``)
                         List of enabled predefeined :ref:`schema` name.

                         For the usage of predefeined schema, please refer to
                         :ref:`predefined-schemas`.

                         If you want to disable all predefeined schemas, set it
                         to ``[]``.
:any_custom_schemas: (Type: ``List[Dict[str,Any]]``, Default: ``[]``)
                     List of enabled custom :ref:`schema`. For the way of writing
                     custom schema, please refer to :ref:`writing-schema`.

Functionalities
===============

.. _schema:

Schema
------

Before descibing any object, we need a "schema" to descibe "how to descibe the object".
For extension user, "schema" is a python ``dict`` that can specific in :file:`conf.py`.
See :ref:`Configuration` for details.

.. _writing-schema:

Writing Schema
--------------

An schema for descibing cat looks like this:

.. literalinclude:: ./cat.py
   :language: python

The aboved schema created a ``cat`` directive under "any" domain that
can descibe a cat.

The created directive accept only one argument, which indicates the name of object,
aliases can be added on a new line after name, one alias per line.

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

**templates**
    Type: ``Dict[str,Any]``, descibes how directive and role will be show.
    We use Jinja_ as templating engine.

    **role**
        Template for rendering role's interpreted text, the origin
        interpreted text appears as ``{{ title }}`` variable when rendering.

    **directive**
        Template for rendering directive's content. the only one argument of
        directive appears as ``{{ name }}`` variable when rendering.
        the origin content appears as ``{{ content }}`` variable when rendering.

        .. note:: ``{{ content }}`` is a string list but not string.

.. _Jinja: https://jinja.palletsprojects.com/

Now we descibe a cat with the newly created directive:

.. literalinclude:: nyan-cat.txt
   :language: rst

It will be rendered as:

.. include:: nyan-cat.txt

Use the ``cat`` role under "any" domain to reference Nyan Cat:

- Reference by name: ``:any:cat:`Nyan Cat``` -> :any:cat:`Nyan Cat`
- Reference by alias: ``:any:cat:`Nyan_Cat``` -> :any:cat:`Nyan_Cat`
- Reference by ID: ``:any:cat:`1``` -> :any:cat:`1`
- Explicit title is supported: ``:any:cat:`This cat <Nyan Cat>``` -> :any:cat:`This cat <Nyan Cat>`

.. _predefined-schemas:

Predefined Schemas
------------------

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

2020-12-20 1.0a1
----------------

 .. sectionauthor:: Shengyu Zhang

The alpha version is out, enjoy~

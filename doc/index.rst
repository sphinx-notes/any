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

The extension provides a domain which allows user creates directive and roles to descibe, reference and index arbitrary object in documentation by writing reStructuredText templates. It is a bit like :py:meth:`sphinx.application.Sphinx.add_object_type`, but more powerful.

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

.. any:confval:: any_domain_name
   :type: str
   :default: 'any'

   Name of the domain.

.. any:confval:: any_schemas
   :type: List[sphinxnotes.any.Schema]
   :default: []

   List of :ref:`schema <schema>` instances. For the way of writing schema definition, please refer to :ref:`writing-schema`.

Functionalities
===============

.. _writing-schema:

Defining Schema
---------------

.. _schema:

.. topic:: What is Schema?

    Before descibing any object, we need a "schema" to tell extension "how to descibe the object". For extension user, "schema" is a :py:class:`python object <any.Schema>` that can specific in configuration value :any:confval:`any_schemas`.

The necessary python classes for writing schema are listed here:

.. autoclass:: any.Schema

   Class-wide shared special keys used in template rendering context:

   .. autoattribute:: any.Schema.TYPE_KEY
   .. autoattribute:: any.Schema.NAME_KEY
   .. autoattribute:: any.Schema.CONTENT_KEY
   .. autoattribute:: any.Schema.TITLE_KEY

   |

.. autoclass:: any.Field

   |

.. autoclass:: any.Field.Form

   .. autoattribute:: any.Field.Form.PLAIN
   .. autoattribute:: any.Field.Form.WORDS
   .. autoattribute:: any.Field.Form.LINES

Documenting Object
------------------

Once a schema created, the corresponding :ref:`directives`, :ref:`roles` and :ref:`indices` will be generated. You can use them to descibe, reference and index object in your documentation.

For the convenience, we use default domain name "any", and we assume that we have the following schema with in :any:confval:`any_schemas`:

.. literalinclude:: ./cat.py
   :language: python


.. _directives:

Directives
~~~~~~~~~~

.. _object-description:

Object Description
^^^^^^^^^^^^^^^^^^

The aboved schema created a Directive_ named with "``domain``-\ ``objtype``" (In this case, it is ``any:cat``) for descibing object(INC, it is cat🐈).

Arguments
   Arguments are used to specify the :any:tmplvar:`name` of the object. The number argument is depends on the name :py:class:`any.Field` of Schema.

   - A ``None`` field means no argument is required
   - For a non-``None`` Field, see :py:attr:`any.Field` for more details

   .. _underscore-argument:

   Specially, If first argument is ``_`` (underscore), the directive must be located after a `Section Title`_, the text of section title is the real first argument.

   In this case, the ``any:cat`` directive accepts multiple argument split by newline.

Options
   All attributes defined in schema are converted to options of directive. Further, they will available in various :ref:`Templates <writing-template>`.

   - A ``None`` field is no allowed for now means no argument is required

     .. hint:: May be changed in the future vesrion.

   - For a non-``None`` Field, see :py:attr:`any.Field` for more details

   In this case, the directive has three options: ``id``, ``color`` and ``picture``.

Content
   Cotent is used to specify the :any:tmplvar:`content` of the object.

   - A ``None`` field means no content is required
   - For a non-``None`` Field, see :py:attr:`any.Field` for more details

   In this case, the directive accepts content.

The directive will be rendered to a reStructuredText snippet, by :ref:`description-template`, then inserted to documentation.

Let's documenting such a cat:

.. literalinclude:: nyan-cat.txt
   :language: rst

It will be rendered as:

.. include:: nyan-cat.txt

.. _Directive: https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#directives
.. _Section Title: https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#sections

.. _roles:

Roles
~~~~~

Same to :ref:`sphinx:xref-syntax`, explicit title ``:role:`title <target>``` is supported by all the Role_\ s. If not explicit title specific, reference title will be rendered by one of :ref:`reference-template`.

.. _Role: https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#interpreted-text

General Reference
^^^^^^^^^^^^^^^^^

The aboved schema created a role named with "``domain``-\ ``objtype``" (In this case, it is ``any:cat``) for creating a reference to :ref:`object-description`. The interpreted text can be value of *any referenceable field*.

=================== =================================== ========================
Reference by name   ``:any:cat:`Nyan Cat```             :any:cat:`Nyan Cat`
By another name     ``:any:cat:`Nyan_Cat```             :any:cat:`Nyan_Cat`
By ID               ``:any:cat:`1```                    :any:cat:`1`
Explicit title      ``:any:cat:`This cat <Nyan Cat>```  :any:cat:`This cat <Nyan Cat>`
A nonexistent cat   ``:any:cat:`mimi```                 :any:cat:`mimi`
=================== =================================== ========================

Field-Specific Reference
^^^^^^^^^^^^^^^^^^^^^^^^

Role "``domain``-\ ``objtype``.\ ``field``" will be created for all referenceable Fields (In this case, it is ``any:cat.name``, ``any:cat.id`` and ``any:cat.color``).

These roles also create reference to :ref:`object-description`. But the interpreted text must be value of field in role's name.

=================== =============================== ============================
Reference by name   ``:any:cat.name:`Nyan Cat```    :any:cat.name:`Nyan Cat`
By ID               ``:any:cat.id:`1```             :any:cat.id:`1`
=================== =============================== ============================

.. _indices:

Indices
~~~~~~~

According to sphinx documentation, we use :ref:`sphinx:ref-role` to create reference to object indices, and the index name should prefixed with domain name.

General Index
^^^^^^^^^^^^^

Index "``domain``-\ ``objtype``" (In this case, it is ``any-cat``) creates reference to object index which grouped by all referenceable field values.

================== ==============
``:ref:`any-cat``` :ref:`any-cat`
================== ==============

Field Specific Index
^^^^^^^^^^^^^^^^^^^^

Index "``domain``-\ ``objtype``.\ ``field``" will be created for all reference Fields (In this case, it is ``any-cat.name``, ``any-cat.id`` and ``any-cat.color``).

These indices create reference to object index which grouped by specific field values.

======================= ===================
``:ref:`any-cat.name``` :ref:`any-cat.name`
``:ref:`any-cat.id```   :ref:`any-cat.id`
======================= ===================

.. _writing-template:

Writing Template
----------------

We use Jinja2_ as our templating engine.

.. _Jinja2: https://jinja.palletsprojects.com/

Currently we need two kinds of template to let .

.. _description-template:

Description Template
~~~~~~~~~~~~~~~~~~~~

Used to generate object description. Can be written in reStructuredText.

.. _reference-template:

Reference Template
~~~~~~~~~~~~~~~~~~

Used to generate object reference. Only plain text is allowed for now.

Reference Template has two various variants:

Missing Reference Template
   Applied when the reference is missing.

   .. hint:: In this template, only variables :any:tmplvar:`objtype` and :any:tmplvar:`title`  are available.

Ambiguous Reference Template
   Applied when the reference is ambiguous.

   .. hint:: In this template, only variables :any:tmplvar:`objtype` and :any:tmplvar:`title`  are available.

Variables
~~~~~~~~~

For the usage of Jinja's variable, please refer to `Jinja2's Variables`_.

.. _Jinja2's Variables: <https://jinja.palletsprojects.com/en/2.11.x/templates/#variables

All attributes defined in schema are available as variables in template. Note the value of variable might be *string or string list* (depends on value of :py:class:`any.Schema.Field.Form`).

Beside, there are some special variable:

.. any:tmplvar:: objtype
   :type: str
   :conf: TYPE_KEY

   Type of object.

.. any:tmplvar:: name
   :type: Union[None,str,List[str]]
   :conf: NAME_KEY

   Name of object.

.. any:tmplvar:: content
   :type: Union[None,str,List[str]]
   :conf: CONTENT_KEY

   Content of object.

.. any:tmplvar:: title
   :type: str
   :conf: TITLE_KEY

   Title of object.

   In :ref:`reference-template`, its value might be overwritten by explicit title.

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

Tips
====

Omit Domain Name
----------------

You can omit the prefixed domain name in directives and roles by setting the ``primary_domain`` to your :any:confval:`any_domain_name` in :file:`conf.py`. For example, you can use `.. cat::` rather than `.. any:cat::`.

Documenting Section and Documentation
-------------------------------------

By using the :ref:`Underscore Argument <underscore-argument>`, you can
document a section and reference to it. For example:

.. code-block:: rst

   ================
   The Story of Art
   ================

   .. book:: _
      :publisher: Phaidon Press; 16th edition (April 9, 1995) 
      :isbn: 0714832472
      :language: English 

You not need to create a reST label by yourself, just use role like ``:book:`The Story of Art```. Beside, it is also a better replacement of  `Bibliographic Fields`_.

.. _Bibliographic Fields: https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#bibliographic-fields

Change Log
==========

2021-06-03 2.0a3
----------------

- Simplify index name (e4d9207)

.. sectionauthor:: Shengyu Zhang

2021-06-03 2.0a3
----------------

- Simplify index name (e4d9207)

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

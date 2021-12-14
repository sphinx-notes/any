
sphinxnotes.any - Sphinx Domain for Descibing Anything
******************************************************

https://github.com/sphinx-notes/any

:version:
   2.2

:copyright:
   Copyright ©2021 by Shengyu Zhang.

:license:
   BSD, see LICENSE for details.

The extension provides a domain which allows user creates directive
and roles to descibe, reference and index arbitrary object in
documentation by writing reStructuredText templates. It is a bit like
https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx.application.Sphinx.add_object_type,
but more powerful.

*  Installation

*  Configuration

*  Functionalities

   *  Defining Schema

   *  Documenting Object

      *  Directives

         *  Object Description

      *  Roles

         *  General Reference

         *  Field-Specific Reference

      *  Indices

         *  General Index

         *  Field Specific Index

   *  Writing Template

      *  Description Template

      *  Reference Template

      *  Variables

      *  Filters

*  Tips

   *  Omit Domain Name

   *  Documenting Section and Documentation

   *  Enrich Object Description

      *  Categorizing and Tagging

*  Change Log

   *  2021-08-18 2.2

   *  2021-06-26 2.1

   *  2021-06-05 2.0

   *  2021-06-03 2.0a3

   *  2021-06-03 2.0a3

   *  2021-05-23 2.0a2

   *  2021-05-23 2.0a1

   *  2021-05-22 2.0a0

   *  2021-02-28 1.1

   *  2021-02-23 1.0

   *  2021-01-28 1.0b0

   *  2020-12-20 1.0a1


Installation
============

Download it from official Python Package Index:

.. code:: console

   $ pip install sphinxnotes-any

Add extension to ``conf.py`` in your sphinx project:

.. code:: python

   extensions = [
             # …
             'sphinxnotes.any',
             # …
             ]

.. _configuration:


Configuration
=============

The extension provides the following configuration:

``any_domain_name``

   :Type:
      ``str``

   :Default:
      ``'any'``

   Name of the domain.

``any_schemas``

   :Type:
      ``List[sphinxnotes.any.Schema]``

   :Default:
      ``[]``

   List of `schema <#schema>`_ instances. For the way of writing
   schema definition, please refer to `Defining Schema
   <#writing-schema>`_.


Functionalities
===============

.. _writing-schema:


Defining Schema
---------------

.. _schema:


What is Schema?
^^^^^^^^^^^^^^^

Before descibing any object, we need a “schema” to tell extension “how
to descibe the object”. For extension user, “schema” is a `python
object <#any.Schema>`_ that can specific in configuration value
`⚙️any_schemas <#confval-any_schemas>`_.

The necessary python classes for writing schema are listed here:

**class any.Schema(objtype, name=Field(form=<Form.PLAIN: 1>,
unique=True, referenceable=True, required=False), attrs={},
content=Field(form=<Form.PLAIN: 1>, unique=False, referenceable=False,
required=False), description_template='{{ content }}',
reference_template='{{ title }}', missing_reference_template='{{ title
}} (missing reference)', ambiguous_reference_template='{{ title }}
(disambiguation)')**

   Create a Schema instance.

   :Parameters:
      *  **objtype**
         (https://docs.python.org/3/library/stdtypes.html#str) – The
         unique type name of object, it will be used as basename of
         corresponding `Directives <#directives>`_, `Roles <#roles>`_
         and `Indices <#indices>`_

      *  **name** (*any.schema.Field*) – Constraints of optional
         object name

      *  **attrs**
         (*Dict**[*https://docs.python.org/3/library/stdtypes.html#str*,
         **any.schema.Field**]*) – Constraints of object attributes

      *  **content** (*any.schema.Field*) – Constraints of object
         content

      *  **description_template**
         (https://docs.python.org/3/library/stdtypes.html#str) – See
         `Description Template <#description-template>`_

      *  **reference_template**
         (https://docs.python.org/3/library/stdtypes.html#str) – See
         `Reference Template <#reference-template>`_

      *  **missing_reference_template**
         (https://docs.python.org/3/library/stdtypes.html#str) – See
         `Reference Template <#reference-template>`_

      *  **ambiguous_reference_template**
         (https://docs.python.org/3/library/stdtypes.html#str) – See
         `Reference Template <#reference-template>`_

   :Return type:
      https://docs.python.org/3/library/constants.html#None

   Class-wide shared special keys used in template rendering context:

   ``TYPE_KEY = 'type'``

      Template variable name of object type

   ``NAME_KEY = 'name'``

      Template variable name of object name

   ``CONTENT_KEY = 'content'``

      Template variable name of object content

   ``TITLE_KEY = 'title'``

      Template variable name of object title

**class any.Field(form=<Form.PLAIN: 1>, unique=False,
referenceable=False, required=False)**

   Describes value constraint of field of Object.

   The value of field can be single or mulitple string.

   :Parameters:
      *  **form** (*any.schema.Field.Form*) – The form of value.

      *  **unique**
         (https://docs.python.org/3/library/functions.html#bool) –

         Whether the field is unique. If true, the value of field must
         be unique within the scope of objects with same type. And it
         will be used as base string of object identifier.

         Only one unique field is allowed in one object type.

         Note: Duplicated value causes a warning when building
            documentation, and the corresponding object cannot be
            referenced correctly.

      *  **referenceable**
         (https://docs.python.org/3/library/functions.html#bool) –
         Whether the field is referenceable. If ture, object can be
         referenced by field value. See `Roles <#roles>`_ for more
         details.

      *  **required**
         (https://docs.python.org/3/library/functions.html#bool) –
         Whether the field is required. If ture, ``ObjectError`` will
         be raised when building documentation if the value is no
         given.

   :Return type:
      https://docs.python.org/3/library/constants.html#None

**class any.Field.Form(value)**

   An enumeration represents various string forms.

   ``PLAIN = 1``

      A single string

   ``WORDS = 2``

      Mulitple string separated by whitespace

   ``LINES = 3``

      Mulitple string separated by newline(``\n``)


Documenting Object
------------------

Once a schema created, the corresponding `Directives <#directives>`_,
`Roles <#roles>`_ and `Indices <#indices>`_ will be generated. You can
use them to descibe, reference and index object in your documentation.

For the convenience, we use default domain name “any”, and we assume
that we have the following schema with in `⚙️any_schemas
<#confval-any_schemas>`_:

.. code:: python

   from textwrap import dedent
   from any import Schema, Field

   cat = Schema('cat',
       name=Field(referenceable=True, form=Field.Form.LINES),
       attrs={
           'id': Field(unique=True, referenceable=True, required=True),
           'color': Field(referenceable=True),
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
       ambiguous_reference_template='😼{{ title }}')

.. _directives:


Directives
~~~~~~~~~~

.. _object-description:


Object Description
""""""""""""""""""

The aboved schema created a `Directive
<https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#directives>`_
named with “``domain``:``objtype``” (In this case, it is ``any:cat``)
for descibing object(INC, it is cat🐈).

Arguments
   Arguments are used to specify the `{{name}} <#tmplvar-name>`_ of
   the object. The number argument is depends on the name `any.Field
   <#any.Field>`_ of Schema.

   *  A ``None`` field means no argument is required

   *  For a non-``None`` Field, see `any.Field <#any.Field>`_ for more
      details

   .. _underscore-argument:

   Specially, If first argument is ``_`` (underscore), the directive
   must be located after a `Section Title
   <https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#sections>`_,
   the text of section title is the real first argument.

   In this case, the ``any:cat`` directive accepts multiple argument
   split by newline.

Options
   All attributes defined in schema are converted to options of
   directive. Further, they will available in various `Templates
   <#writing-template>`_.

   *  A ``None`` field is no allowed for now means no argument is
      required

      Hint: May be changed in the future vesrion.

   *  For a non-``None`` Field, see `any.Field <#any.Field>`_ for more
      details

   In this case, the directive has three options: ``id``, ``color``
   and ``picture``.

Content
   Content is used to specify the `{{content}} <#tmplvar-content>`_ of
   the object.

   *  A ``None`` field means no content is required

   *  For a non-``None`` Field, see `any.Field <#any.Field>`_ for more
      details

   In this case, the directive accepts content.

The directive will be rendered to a reStructuredText snippet, by
`Description Template <#description-template>`_, then inserted to
documentation.

Let’s documenting such a cat:

.. code:: rst

   .. any:cat:: Nyan Cat
                Nyan_Cat
      :id: 1
      :color: pink gray
      :picture: _images/nyan-cat.gif

      Nyan Cat is the name of a YouTube video uploaded in April 2011,
      which became an internet meme. The video merged a Japanese pop song with
      an animated cartoon cat with a Pop-Tart for a torso, flying through space,
      and leaving a rainbow trail behind it. The video ranked at number 5 on
      the list of most viewed YouTube videos in 2011. [#]_

      .. [#] https://en.wikipedia.org/wiki/Nyan_Cat

It will be rendered as:

``Nyan Cat``

   .. image:: _images/nyan-cat.gif

   :Cat ID:
      1

   :Color:
      pink gray

   Nyan Cat is the name of a YouTube video uploaded in April 2011,
   which became an internet meme. The video merged a Japanese pop song
   with an animated cartoon cat with a Pop-Tart for a torso, flying
   through space, and leaving a rainbow trail behind it. The video
   ranked at number 5 on the list of most viewed YouTube videos in
   2011. [1]

   [1] https://en.wikipedia.org/wiki/Nyan_Cat

.. _roles:


Roles
~~~~~

Same to
https://www.sphinx-doc.org/en/master/usage/restructuredtext/roles.html#xref-syntax,
explicit title ``:role:`title <target>``` is supported by all the
`Role
<https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#interpreted-text>`_s.
If not explicit title specific, reference title will be rendered by
one of `Reference Template <#reference-template>`_.


General Reference
"""""""""""""""""

The aboved schema created a role named with “``domain``-``objtype``”
(In this case, it is ``any:cat``) for creating a reference to `Object
Description <#object-description>`_. The interpreted text can be value
of *any referenceable field*.

+---------------------+-------------------------------------+--------------------------------+
| Reference by name   | ``:any:cat:`Nyan Cat```             | `🐈Nyan Cat <#cat-1>`_          |
+---------------------+-------------------------------------+--------------------------------+
| By another name     | ``:any:cat:`Nyan_Cat```             | `🐈Nyan Cat <#cat-1>`_          |
+---------------------+-------------------------------------+--------------------------------+
| By ID               | ``:any:cat:`1```                    | `🐈Nyan Cat <#cat-1>`_          |
+---------------------+-------------------------------------+--------------------------------+
| Explicit title      | ``:any:cat:`This cat <Nyan Cat>```  | `This cat <#cat-1>`_           |
+---------------------+-------------------------------------+--------------------------------+
| A nonexistent cat   | ``:any:cat:`mimi```                 | ``😿mimi``                      |
+---------------------+-------------------------------------+--------------------------------+


Field-Specific Reference
""""""""""""""""""""""""

Role “``domain``-``objtype``.``field``” will be created for all
referenceable Fields (In this case, it is ``any:cat.name``,
``any:cat.id`` and ``any:cat.color``).

These roles also create reference to `Object Description
<#object-description>`_. But the interpreted text must be value of
field in role’s name.

+---------------------+---------------------------------+------------------------------+
| Reference by name   | ``:any:cat.name:`Nyan Cat```    | `🐈Nyan Cat <#cat-1>`_        |
+---------------------+---------------------------------+------------------------------+
| By ID               | ``:any:cat.id:`1```             | `🐈Nyan Cat <#cat-1>`_        |
+---------------------+---------------------------------+------------------------------+

.. _indices:


Indices
~~~~~~~

According to sphinx documentation, we use
https://www.sphinx-doc.org/en/master/usage/restructuredtext/roles.html#ref-role
to create reference to object indices, and the index name should
prefixed with domain name.


General Index
"""""""""""""

Index “``domain``-``objtype``” (In this case, it is ``any-cat``)
creates reference to object index which grouped by all referenceable
field values.

+--------------------+-----------------+
| ``:ref:`any-cat``` | `Cat Reference  |
+--------------------+-----------------+


Field Specific Index
""""""""""""""""""""

Index “``domain``-``objtype``.``field``” will be created for all
reference Fields (In this case, it is ``any-cat.name``, ``any-cat.id``
and ``any-cat.color``).

These indices create reference to object index which grouped by
specific field values.

+-------------------------+----------------------+
| ``:ref:`any-cat.name``` | `Cat Name Reference  |
+-------------------------+----------------------+
| ``:ref:`any-cat.id```   | `Cat Id Reference    |
+-------------------------+----------------------+

.. _writing-template:


Writing Template
----------------

We use `Jinja <https://jinja.palletsprojects.com/>`_ as our templating
engine.

Currently we need two kinds of template to let .

.. _description-template:


Description Template
~~~~~~~~~~~~~~~~~~~~

Used to generate object description. Can be written in
reStructuredText.

.. _reference-template:


Reference Template
~~~~~~~~~~~~~~~~~~

Used to generate object reference. Only plain text is allowed for now.

Reference Template has two various variants:

Missing Reference Template
   Applied when the reference is missing.

   Hint: In this template, only variables `{{objtype}}
      <#tmplvar-objtype>`_ and `{{title}} <#tmplvar-title>`_  are
      available.

Ambiguous Reference Template
   Applied when the reference is ambiguous.

   Hint: In this template, only variables `{{objtype}}
      <#tmplvar-objtype>`_ and `{{title}} <#tmplvar-title>`_  are
      available.


Variables
~~~~~~~~~

For the usage of Jinja’s variable, please refer to `Jinja's Variables
<<https://jinja.palletsprojects.com/en/2.11.x/templates/#variables>`_.

All attributes defined in schema are available as variables in
template. Note the value of variable might be *string or string list*
(depends on value of ``any.Schema.Field.Form``).

Beside, there are some special variable:

``objtype``

   :Type:
      ``str``

   Type of object.

   Tip: Name of variables(“objtype”) can be changed by setting `TYPE_KEY
      <#any.Schema.TYPE_KEY>`_

``name``

   :Type:
      ``Union[None,str,List[str]]``

   Name of object.

   Tip: Name of variables(“name”) can be changed by setting `NAME_KEY
      <#any.Schema.NAME_KEY>`_

``content``

   :Type:
      ``Union[None,str,List[str]]``

   Content of object.

   Tip: Name of variables(“content”) can be changed by setting
      `CONTENT_KEY <#any.Schema.CONTENT_KEY>`_

``title``

   :Type:
      ``str``

   Title of object.

   In `Reference Template <#reference-template>`_, its value might be
   overwritten by explicit title.

   Tip: Name of variables(“title”) can be changed by setting `TITLE_KEY
      <#any.Schema.TITLE_KEY>`_


Filters
~~~~~~~

For the usage of Jinja’s filter, please refer to `Jinja's Filters
<https://jinja.palletsprojects.com/en/2.11.x/templates/#filters>>`_.

All `Jinja's Builtin Filters
<https://jinja.palletsprojects.com/en/2.11.x/templates/#builtin-filters>`_
are available. In additional, we provide the following custom filters
to enhance the template:

``copyfile(fn)``
   Copy a file in Sphinx srcdir to outdir, return the URI of file
   which relative to current documentation.

   The relative path to srcdir will be preserved, for example, ``{{ fn
   | copyfile }}`` while ``fn`` is ``_images/foo.jpg``, the file will
   copied to ``<OUTDIR>/_any/_images/foo.jpg``, and returns a POSIX
   path of ``fn`` which relative to current documentation.

``thumbnail(img, width, height)``
      Changes the size of an image to the given dimensions and removes
      any associated profiles, returns a a POSIX path of thumbnail
      which relative to current documentation.

      This filter always keep the origin aspect ratio of image. The
      width and height are optional, By default are 1280 and 720
      respectively.

   New in version 1.0.


Tips
====


Omit Domain Name
----------------

You can omit the prefixed domain name in directives and roles by
setting the ``primary_domain`` to your `⚙️any_domain_name
<#confval-any_domain_name>`_ in ``conf.py``. For example, you can use
``.. cat::`` rather than ``.. any:cat::``.


Documenting Section and Documentation
-------------------------------------

By using the `Underscore Argument <#underscore-argument>`_, you can
document a section and reference to it. For example:

.. code:: rst

   ================
   The Story of Art
   ================

   .. book:: _
      :publisher: Phaidon Press; 16th edition (April 9, 1995)
      :isbn: 0714832472
      :language: English

You not need to create a reST label by yourself, just use role like
``:book:`The Story of Art```. Beside, it is also a better replacement
of  `Bibliographic Fields
<https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#bibliographic-fields>`_.


Enrich Object Description
-------------------------

As the `Description Template <#description-template>`_ supports
reStructuredText, We have a lot of room to play.


Categorizing and Tagging
~~~~~~~~~~~~~~~~~~~~~~~~

When we descibing a object, usually we are categorizing and tagging
them. For dog, we may define such a Schema:

.. code:: python

   from textwrap import dedent
   from any import Schema, Field

   dog = Schema('dog',
       attrs={
           'breed': Field(referenceable=True),
           'color': Field(referenceable=True, form=Field.Form.WORDS),
       },
       description_template=dedent("""
           :Breed: {{ breed }}
           :Colors: {{ colors }}"""),
       reference_template='🐕{{ title }}',
       ambiguous_reference_template='{{ title }}')

The field ``breed`` is a category and ``colors`` is a serial of tags.
We are really categorizing and tagging dogs but, it is a quite boring.
Considering the following object description:

.. code:: rst

   .. any:dog:: Indiana
      :breed: Husky
      :color: Black White

When we see the breed of Indiana is “Husky”, we may want to see what
other huskies. When we see the colors of Indiana is “Black” and
“White”, We will have the same idea. So, let’s create references for
these values:

.. code:: python

   from textwrap import dedent
   from any import Schema, Field

   dog = Schema('dog',
       attrs={
           'breed': Field(referenceable=True),
           'color': Field(referenceable=True, form=Field.Form.WORDS),
       },
       description_template=dedent("""
           :Breed: :any:dog.breed:`{{ breed }}`
           :Colors: {% for c in color %}:any:dog.color:`{{ c }}` {% endfor %}"""),
       reference_template='🐕{{ title }}',
       ambiguous_reference_template='{{ title }}')

For field breed, its value is a string, so we simpily wrap value in to
a ``any:dog.breed`` role, In this case it create a reference to all
Husky dog.

For field color, its value is a string list, we have to iterate it and
wrap element to to a ``any:dog.color`` role, In this case it create a
reference to all Black dog and White dog.

The rendered reStructuredText looks like this:

.. code:: rst

   :Breed: :any:dog.breed:`Husky`
   :Colors: :any:dog.color:`Black` any:dog.color:`White`

The rendered object description:

``Indiana``

   :Breed:
      `Husky <any-dog.breed.rst#cap-Husky>`_

   :Colors:
      `Black <any-dog.color.rst#cap-Black>`_ `White
      <any-dog.color.rst#cap-White>`_


Change Log
==========


2021-08-18 2.2
--------------

*  Use the Object ID as index name when no object title available


2021-06-26 2.1
--------------

*  Report ambiguous object via debug log

*  Some doc fixes

*  Remove unused import


2021-06-05 2.0
--------------

*  Update documentation, add some tips


2021-06-03 2.0a3
----------------

*  Simplify index name (e4d9207)


2021-06-03 2.0a3
----------------

*  Simplify index name (e4d9207)


2021-05-23 2.0a2
----------------

*  Fix none object signture (6a5f75f)

*  Prevent sphinx config changed everytime (f7b316b)


2021-05-23 2.0a1
----------------

*  Template variable must be non None (fb9678e)

*  Template will not apply on role with explicit title (5bdaad1)


2021-05-22 2.0a0
----------------

*  Descibing schema with python object instead of dict

*  Support index

*  Refactor


2021-02-28 1.1
--------------

*  Remove symbol link if exists


2021-02-23 1.0
--------------

*  Move preset schemas to standalone package

*  Add custom filter support to template

*  Combine ``any_predefined_schemas`` and ``any_custom_schemas`` to
   ``any_schemas``


2021-01-28 1.0b0
----------------

*  Fix the missing Jinja dependency

*  Use section title as object name when directive argument is omitted

*  Some code cleanups

*  Rename schema field “role” to “reference”

*  Rename schema field “directive” to “content”


2020-12-20 1.0a1
----------------

The alpha version is out, enjoy~

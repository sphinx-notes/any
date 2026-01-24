=====
Usage
=====

.. warning:: Still WIP.

.. _writing-objdef:

Object Type Definiton
=====================

Before descibing any object, we need to tell extension "what data consist of the object and how to display it".

The object type definiton does this. A definition is a python dict, consists of two main parts: Schema (Data) and Templates (Presentation):

.. literalinclude:: /_schemas/cat.py

The Field Definiton DSL
-----------------------

Documenting Object
==================

Once a schema created, the corresponding :ref:`directives`, :ref:`roles` and :ref:`indices` will be generated. You can use them to descibe, reference and index object in your documentation.

For the convenience, we use default domain name "any", and we assume that we have the following schema with in :obj:confval:`any_schemas`:

.. _directives:

Directives
----------

.. _object-description:

Object Description
~~~~~~~~~~~~~~~~~~

The aboved schema created a Directive_ named with "``domain``:\ ``objtype``" (In this case, it is ``obj:cat``) for descibing object(INC, it is cat🐈).

Arguments
   Arguments are used to specify the :obj:tmplvar:`name` of the object. The number argument is depends on the name :py:class:`any.Field` of Schema.

   - A ``None`` field means no argument is required
   - For a non-``None`` Field, see :py:attr:`any.Field` for more details

   .. _underscore-argument:

   Specially, If first argument is ``_`` (underscore), the directive must be located after a `Section Title`_, the text of section title is the real first argument.

   In this case, the ``obj:cat`` directive accepts multiple argument split by newline.

Options
   All attributes defined in schema are converted to options of directive. Further, they will available in various :ref:`Templates <writing-template>`.

   - A ``None`` field is no allowed for now means no argument is required

     .. hint:: May be changed in the future vesrion.

   - For a non-``None`` Field, see :py:attr:`any.Field` for more details

   In this case, the directive has three options: ``id``, ``color`` and ``picture``.

Content
   Content is used to specify the :obj:tmplvar:`content` of the object.

   - A ``None`` field means no content is required
   - For a non-``None`` Field, see :py:attr:`any.Field` for more details

   In this case, the directive accepts content.

The directive will be rendered to a reStructuredText snippet, by :ref:`description-template`, then inserted to documentation.

Let's documenting such a cat:

.. literalinclude:: /_schemas/nyan-cat.txt
   :language: rst

It will be rendered as:

.. include:: /_schemas/nyan-cat.txt

.. _Directive: https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#directives
.. _Section Title: https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#sections

.. _roles:

Roles
-----

Same to :ref:`sphinx:xref-syntax`, explicit title ``:role:`title <target>``` is supported by all the Role_\ s. If not explicit title specific, reference title will be rendered by one of :ref:`reference-template`.

.. _Role: https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#interpreted-text

General Reference
~~~~~~~~~~~~~~~~~

The aboved schema created a role named with "``domain``-\ ``objtype``" (In this case, it is ``obj:cat``) for creating a reference to :ref:`object-description`. The interpreted text can be value of *any referenceable field*.

=================== =================================== ========================
Reference by name   ``:obj:cat:`Nyan Cat```             :obj:cat:`Nyan Cat`
By another name     ``:obj:cat:`Nyan_Cat```             :obj:cat:`Nyan_Cat`
By ID               ``:obj:cat:`1```                    :obj:cat:`1`
Explicit title      ``:obj:cat:`This cat <Nyan Cat>```  :obj:cat:`This cat <Nyan Cat>`
A nonexistent cat   ``:obj:cat:`mimi```                 :obj:cat:`mimi`
=================== =================================== ========================

Field-Specific Reference
~~~~~~~~~~~~~~~~~~~~~~~~

Role "``domain``-\ ``objtype``.\ ``field``" will be created for all referenceable Fields (In this case, it is ``obj:cat.name``, ``any:cat.id`` and ``any:cat.color``).

These roles also create reference to :ref:`object-description`. But the interpreted text must be value of field in role's name.

=================== =============================== ============================
Reference by name   ``:obj:cat.name:`Nyan Cat```    :obj:cat.name:`Nyan Cat`
By ID               ``:obj:cat.id:`1```             :obj:cat.id:`1`
=================== =============================== ============================

.. _indices:

Indices
-------

According to sphinx documentation, we use :ref:`sphinx:ref-role` to create reference to object indices, and the index name should prefixed with domain name.

General Index
~~~~~~~~~~~~~

Index "``domain``-\ ``objtype``" (In this case, it is ``any-cat``) creates reference to object index which grouped by all referenceable field values.

================== ==============
``:ref:`any-cat``` :ref:`any-cat`
================== ==============

Field Specific Index
~~~~~~~~~~~~~~~~~~~~

Index "``domain``-\ ``objtype``.\ ``field``" will be created for all reference Fields (In this case, it is ``any-cat.name``, ``any-cat.id`` and ``any-cat.color``).

These indices create reference to object index which grouped by specific field values.

======================= ===================
``:ref:`any-cat.name``` :ref:`any-cat.name`
``:ref:`any-cat.id```   :ref:`any-cat.id`
======================= ===================

.. _writing-template:

Writing Template
================

We use Jinja_ as our templating engine.

.. _Jinja: https://jinja.palletsprojects.com/

Currently we need two kinds of template to let .

.. _description-template:

Description Template
--------------------

Used to generate object description. Can be written in reStructuredText.

.. _reference-template:

Reference Template
------------------

Used to generate object reference. Only plain text is allowed for now.

Reference Template has two various variants:

Missing Reference Template
   Applied when the reference is missing.

   .. hint:: In this template, only variables :obj:tmplvar:`objtype` and :obj:tmplvar:`title`  are available.

Ambiguous Reference Template
   Applied when the reference is ambiguous.

   .. hint:: In this template, only variables :obj:tmplvar:`objtype` and :obj:tmplvar:`title`  are available.

Variables
---------

For the usage of Jinja's variable, please refer to `Jinja's Variables`_.

.. _Jinja's Variables: <https://jinja.palletsprojects.com/en/2.11.x/templates/#variables

All attributes defined in schema are available as variables in template. Note the value of variable might be *string or string list* (depends on value of :py:class:`any.Schema.Field.Form`).

Beside, there are some special variable:

.. obj:tmplvar:: objtype
   :type: str
   :conf: TYPE_KEY

   Type of object.

.. obj:tmplvar:: name
   :type: Union[None,str,List[str]]
   :conf: NAME_KEY

   Name of object.

.. obj:tmplvar:: content
   :type: Union[None,str,List[str]]
   :conf: CONTENT_KEY

   Content of object.

.. obj:tmplvar:: title
   :type: str
   :conf: TITLE_KEY

   Title of object.

   In :ref:`reference-template`, its value might be overwritten by explicit title.

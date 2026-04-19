=====
Usage
=====

``sphinxnotes-any`` lets you define object types in :file:`conf.py`.
For each object type, it creates Sphinx domain objects: directives for defining
objects, roles for cross-referencing them, and indices for browsing them.

The data parsing and template rendering are provided by
:external+render:ref:`sphinxnotes.render <framework>`. This page focuses on the
``any`` domain behavior. For the shared field DSL and Jinja template semantics,
refer to :external+render:doc:`dsl` and :external+render:doc:`tmpl`.

.. highlight:: rst

.. _writing-objdef:

Defining Object Types
=====================

Object types are configured through :confval:`any_object_types`. Each entry has
a ``schema`` section and a ``templates`` section:

.. literalinclude:: /_schemas/cat.py
   :language: python

The dictionary key, ``cat`` in this example, becomes the object type name. With
the default :confval:`any_domain_name`, the extension registers the directive
``.. any:cat::`` and the role ``:any:cat:``.

Schema
------

The ``schema`` section describes the data accepted by the generated directive.
It has three parts:

``name``
   The directive argument. Use ``None`` when the object has no name argument.

``attrs``
   A mapping from directive option names to field declarations.

``content``
   The directive body. Use ``None`` when the object must not have content.

Field declarations use the Field Description Language from
``sphinxnotes-render``. See :external+render:doc:`dsl` for the built-in types,
forms, flags, and by-options.

``sphinxnotes-any`` adds these field modifiers on top of the render DSL:

``ref``
   The field value can be used as a cross-reference target. Aliases:
   ``refer``, ``referable``, ``referenceable``.

``uniq``
   The field value is the unique identifier of the object. Only one field in a
   schema can use this flag. Alias: ``unique``.

``index by <name>``
   Create an additional role and index using a named indexer. Alias:
   ``idx by <name>``.

Templates
---------

The ``templates`` section controls how an object is rendered:

``obj``
   Renders the object body inserted by the object directive.

``header``
   Renders the object signature or the section title used as the object name.
   Use ``None`` to disable the header template.

``ref``
   Renders cross-reference text.

``ref_by``
   A mapping from field names to field-specific reference templates.

``embed``
   Default template for ``.. any:cat+embed::``. Use ``None`` when embedded
   output must always be supplied inline.

``debug``
   Enables render debug output for the object type.

Templates are Jinja text rendered by ``sphinxnotes-render``. In normal object
templates, ``{{ name }}``, ``{{ attrs }}``, every attribute field lifted from
``attrs``, and ``{{ content }}`` are available. Cross-reference templates are
rendered during the resolving phase, so they can also use the explicit reference
title as ``{{ title }}``. See :external+render:doc:`tmpl` for the complete
template model and :external+render:ref:`render-phases`.

.. _directives:

Documenting Objects
===================

For every configured object type, ``sphinxnotes-any`` registers a directive
named ``<domain>:<object-type>``. With the default domain and the ``cat`` object
type, use ``.. any:cat::``:

.. literalinclude:: /_schemas/nyan-cat.txt
   :language: rst

It is rendered as:

.. include:: /_schemas/nyan-cat.txt

The generated directive follows the object schema:

``name``
   Becomes the directive argument. If the argument is ``_`` or omitted where the
   schema requires a scalar name, ``sphinxnotes-any`` can take the nearest
   section title as the object name. See :ref:`underscore-argument`.

``attrs``
   Become directive options.

``content``
   Becomes the directive body.

.. _object-description:

The rendered object is stored in the ``any`` domain. Its anchor and reference
values are derived from the ``uniq`` and ``ref`` fields.

.. _roles:

Referencing Objects
===================

A field marked with ``ref`` creates cross-reference roles.

The all-in-one role uses the object type name, such as ``:any:cat:``. It can
resolve a value from any referenceable field:

.. example::
   :style: grid

   Reference by name
      :any:cat:`Nyan Cat`
   Explicit title
      :any:cat:`This cat <Nyan Cat>`

Field-specific roles use ``<object-type>.<field>``. They only resolve values
from the named field:

.. example::
   :style: grid

   Reference by name
      :any:cat.name:`Nyan Cat`
   Reference by color
      :any:cat.color:`rainbow`

If a reference value matches multiple objects, the reference points to the
corresponding object index instead of choosing one object arbitrarily.

.. _indices:

Browsing Object Indices
=======================

Each referenceable field creates an object index. Use :rst:role:`ref` to link
to an index page.

General indices are named ``<domain>-<object-type>``:

.. example::
   :style: grid

   Browse all cats
      :ref:`any-cat`

Field-specific indices are named ``<domain>-<object-type>.<field>``:

.. example::
   :style: grid

   Browse cats by name
      :ref:`any-cat.name`
   Browse cats by color
      :ref:`any-cat.color`

Additional indices configured with ``index by <name>`` are named
``<domain>-<object-type>.<field>+by-<indexer>``. Built-in indexers are:

``literal``
   Group by the literal field value. This is the default indexer.

``dot``
   Group dotted paths into one level of hierarchy.

``slash``
   Group slash-separated paths into one level of hierarchy.

``year``
   Group ``date`` values by year, month, and day.

``month``
   Group ``date`` values by month and day.

.. _embedding-objects:

Embedding Objects
=================

For every object type, the extension also registers
``.. <domain>:<object-type>+embed::``. It resolves an existing object and renders
it with the configured ``embed`` template or with inline directive content.
When no ``embed`` template is configured, provide the template inline:

.. example::
   :style: grid

   .. any:cat+embed:: mimi

      Embedded cat: **{{ name }}**.

Use embedding when the same object needs a compact representation in another
page or section.

Debugging Templates
===================

Set ``debug`` to ``True`` in an object type definition to enable render debug
output for all of its templates:

.. code-block:: python

   any_object_types = {
       'cat': {
           'schema': {
               'name': 'str, ref, uniq',
           },
           'templates': {
               'obj': '{{ name }}',
               'ref': '{{ title }}',
           },
           'debug': True,
       },
   }

For lower-level details about context construction and rendering phases, see
:external+render:doc:`tmpl`.

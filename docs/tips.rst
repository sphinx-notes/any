====
Tips
====

Omit Domain Name
================

You can omit the domain prefix in directives and roles by setting
``primary_domain`` to :confval:`any_domain_name` in :file:`conf.py`:

.. code-block:: python

   primary_domain = 'any'

Then ``.. cat::`` and ``:cat:`mimi``` are equivalent to ``.. any:cat::`` and
``:any:cat:`mimi```.

.. _underscore-argument:

Documenting Section and Documentation
=====================================

Use ``_`` as the first argument when the object should be attached to the
nearest section title. The section title becomes the object name and can be
referenced like any other object:

.. code-block:: rst

   ================
   The Story of Art
   ================

   .. book:: _
      :publisher: Phaidon Press; 16th edition (April 9, 1995) 
      :isbn: 0714832472
      :language: English

You do not need to create a reStructuredText label manually. Use a role such as
``:book:`The Story of Art``` to reference the section object.

This pattern is useful when a section itself is the thing being documented:
books, papers, projects, releases, glossary entries, or long-form notes. It is
also a structured replacement for simple `Bibliographic Fields`_.

.. _Bibliographic Fields: https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#bibliographic-fields

Enrich Object Description
=========================

Object templates are rendered as reStructuredText, so a template can create
links, field lists, admonitions, cards, or any other markup that Sphinx can
parse. For template syntax and available context variables, see
:external+render:doc:`tmpl`.

Categorizing and Tagging
------------------------

Mark category and tag fields as ``ref`` when users should be able to browse all
objects with the same value.

For example, this dog object type has a category-like ``breed`` field and a
tag-like ``color`` field:

.. literalinclude:: /_schemas/dog1.py
   :language: python

This records structured data, but the rendered object does not yet link those
values. To make the category and tags navigable, reference them from the object
template:

.. literalinclude:: /_schemas/dog2.py
   :language: python

For the scalar ``breed`` field, wrap the value in the field-specific role
``:any:dog.breed:``. For the list-like ``color`` field, iterate over the values
and wrap each value in ``:any:dog.color:``.

The rendered reStructuredText is equivalent to:

.. code-block:: rst

   :Breed: :any:dog.breed:`Husky`
   :Colors: :any:dog.color:`Black` :any:dog.color:`White`

The object can still be written as plain structured data:

.. literalinclude:: /_schemas/indiana-dog.txt
   :language: rst

It will be rendered as:

.. include:: /_schemas/indiana-dog.txt

Path and Date Indices
=====================

The default index groups objects by literal reference values. For hierarchical
or chronological fields, add ``index by <indexer>`` to the field declaration:

.. code-block:: python

   any_object_types = {
       'note': {
           'schema': {
               'name': 'str, ref, uniq',
               'attrs': {
                   'path': 'str, ref, index by slash',
                   'created': 'date, ref, index by year, index by month',
               },
           },
           'templates': {
               'obj': '{{ content }}',
               'ref': '{{ title }}',
           },
       },
   }

This creates the regular roles and indices for ``path`` and ``created``, plus
additional roles and indices:

``:any:note.path+by-slash:`guide/install```
   Resolves a path value and can fall back to the slash-grouped path index when
   the value is ambiguous.

``:ref:`any-note.path+by-slash```
   Links to the slash-grouped path index.

``:ref:`any-note.created+by-year```
   Links to the year-grouped date index.

``:ref:`any-note.created+by-month```
   Links to the month-grouped date index.

The ``date`` type accepts ``YYYY-MM-DD``, ``YYYY-MM``, and ``YYYY`` by default.

Keep Render Details in Render Docs
==================================

``sphinxnotes-any`` is built on top of ``sphinxnotes-render``. When writing user
documentation for an ``any`` object type, link to render concepts instead of
copying their details:

``:external+render:doc:`dsl```
   Field Description Language: types, forms, flags, and by-options.

``:external+render:doc:`tmpl```
   Jinja template context, extra context, filters, and render phases.

``:external+render:ref:`render-phases```
   When parsing, parsed, and resolving templates are executed.

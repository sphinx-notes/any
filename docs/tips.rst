====
Tips
====

Omit Domain Name
================

You can omit the prefixed domain name in directives and roles by setting the ``primary_domain`` to your :any:confval:`any_domain_name` in :file:`conf.py`. For example, you can use ``.. cat::`` rather than ``.. any:cat::``.

Documenting Section and Documentation
=====================================

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

Enrich Object Description
=========================

As the :ref:`description-template` supports reStructuredText, We have a lot of room to play.

Categorizing and Tagging
------------------------

When we descibing a object, usually we are categorizing and tagging them.
For dog, we may define such a Schema: 

.. literalinclude:: /_schemas/dog1.py
   :language: python

The field ``breed`` is a category and ``colors`` is a serial of tags.  We are really categorizing and tagging dogs but, it is a quite boring.  Considering the following object description:

.. literalinclude:: /_schemas/indiana-dog.txt
   :language: rst

When we see the breed of Indiana is "Husky", we may want to see what other huskies. When we see the colors of Indiana is "Black" and "White", We will have the same idea. So, let's create references for these values:

.. literalinclude:: /_schemas/dog2.py
   :language: python

For field breed, its value is a string, so we simpily wrap value in to a ``any:dog.breed`` role, In this case it create a reference to all Husky dog.

For field color, its value is a string list, we have to iterate it and wrap element to to a ``any:dog.color`` role, In this case it create a reference to all Black dog and White dog.

The rendered reStructuredText looks like this:

.. code-block:: rst

   :Breed: :any:dog.breed:`Husky`
   :Colors: :any:dog.color:`Black` any:dog.color:`White`

The rendered object description:

.. include:: /_schemas/indiana-dog.txt

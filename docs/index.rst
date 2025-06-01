.. This file is generated from sphinx-notes/cookiecutter.
   You need to consider modifying the TEMPLATE or modifying THIS FILE.

===============
sphinxnotes-any
===============

.. |docs| image:: https://img.shields.io/github/deployments/sphinx-notes/any/github-pages?label=docs
   :target: https://sphinx.silverrainz.me/any
   :alt: Documentation Status
.. |license| image:: https://img.shields.io/github/license/sphinx-notes/any
   :target: https://github.com/sphinx-notes/any/blob/master/LICENSE
   :alt: Open Source License
.. |pypi| image:: https://img.shields.io/pypi/v/sphinxnotes-any.svg
   :target: https://pypi.python.org/pypi/sphinxnotes-any
   :alt: PyPI Package
.. |download| image:: https://img.shields.io/pypi/dm/sphinxnotes-any
   :target: https://pypi.python.org/pypi/sphinxnotes-any
   :alt: PyPI Package Downloads
.. |github| image:: https://img.shields.io/badge/GitHub-181717?style=flat&logo=github&logoColor=white/
   :target: https://github.com/sphinx-notes/any
   :alt: GitHub Repository

|docs| |license| |pypi| |download| |github|
 
Introduction
============

.. INTRODUCTION START

The extension provides a domain which allows user creates directive and roles 
to descibe, reference and index arbitrary object in documentation.
It is a bit like :py:meth:`sphinx.application.Sphinx.add_object_type`,
but more powerful.

.. INTRODUCTION END

Getting Started
===============

.. note::

   We assume you already have a Sphinx documentation,
   if not, see `Getting Started with Sphinx`_.


First, downloading extension from PyPI:

.. code-block:: console

   $ pip install sphinxnotes-any


Then, add the extension name to ``extensions`` configuration item in your
:parsed_literal:`conf.py_`:

.. code-block:: python

   extensions = [
             # …
             'sphinxnotes.any',
             # …
             ]

.. _Getting Started with Sphinx: https://www.sphinx-doc.org/en/master/usage/quickstart.html
.. _conf.py: https://www.sphinx-doc.org/en/master/usage/configuration.html

.. ADDITIONAL CONTENT START

See :doc:`usage` and :doc:`conf` for more details.

.. ADDITIONAL CONTENT END

Contents
========

.. toctree::
   :caption: Contents

   usage
   conf   
   tips   
   changelog

The Sphinx Notes Project
========================

The project is developed by `Shengyu Zhang`__,
as part of **The Sphinx Notes Project**.

.. toctree::
   :caption: The Sphinx Notes Project

   Home <https://sphinx.silverrainz.me/>
   Blog <https://silverrainz.me/blog/category/sphinx.html>
   PyPI <https://pypi.org/search/?q=sphinxnotes>

__ https://github.com/SilverRainZ

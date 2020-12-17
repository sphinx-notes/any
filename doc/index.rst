==========================
Sphinx Domain for Anything
==========================

.. image:: https://img.shields.io/github/stars/sphinx-notes/any.svg?style=social&label=Star&maxAge=2592000
   :target: https://github.com/sphinx-notes/any

:version: |version|
:copyright: Copyright ©2020 by Shengyu Zhang.
:license: BSD, see LICENSE for details.

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

Functionalities
===============

Configuration
=============

Examples
========

.. any:friend:: SilverRainZ
                LA
                谷月轩
   :blog: https://silverrainz.me
   :avatar: _images/sphinx-notes.png
    
   Former programmer,
   10% stream processing,
   10% distributed system,
   and 80% fool.

My friend :any:friend:`SilverRainZ`

Chang Log
=========

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
   :avatar: _images/sphinx-notes.png
   :blog: https://silverrainz.me
   :github: SilverRainZ
    
   Former programmer,
   10% stream processing,
   10% distributed system,
   and 80% fool.


.. any:book:: 德米安
              德米安：埃米尔·辛克莱的彷徨少年时
   :isbn: 9787208081550

   黑塞的代表作之一，讲述少年辛克莱寻找通向自身之路的艰辛历程。
   出生并成长于“光明世界”的辛克莱，偶然发现截然不同的“另一个世界”，
   那里的纷乱和黑暗，使他焦虑困惑，并陷入谎言带来的灾难之中。
   这时，一个名叫德米安的少年出现，将他带出沼泽地，
   从此他开始走向孤独寻找自我的前路。
   之后的若干年，“德米安”以不同的身份面目出现，
   在他每一次孤独寻找、艰难抉择的时候，成为他的引路人……

:any:friend:`SilverRainZ` likes :any:book:`德米安`. :any:book:`9787208081550`.


Chang Log
=========

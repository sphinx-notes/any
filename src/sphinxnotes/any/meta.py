# This file is generated from sphinx-notes/cookiecutter.
# DO NOT EDIT!!!

################################################################################
# Project meta infos.
################################################################################

from __future__ import annotations
from importlib import metadata

__project__ = 'sphinxnotes-any'
__author__ = 'Shengyu Zhang'
__desc__ = 'Sphinx domain for documenting anything'

try:
    __version__ = metadata.version('sphinxnotes-any')
except metadata.PackageNotFoundError:
    __version__ = 'unknown'

#
################################################################################
# Sphinx extension utils.
################################################################################


def pre_setup(app):
    app.require_sphinx('7.0')


def post_setup(app):
    return {
        'version': __version__,
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }


#

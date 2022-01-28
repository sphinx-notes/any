"""
    sphinxnotes.any.template
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Jinja template extensions for sphinxnotes.any.

    :copyright: Copyright 2021 Shengyu Zhang
    :license: BSD, see LICENSE for details.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Tuple

import os
from os import path
import posixpath
import tempfile
import shutil

from sphinx.util import ensuredir, relative_uri
if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.builders import Builder

import jinja2
from wand.image import Image

ANYDIR = '_any'

class Environment(jinja2.Environment):
    _builder:Builder
    # Exclusive outdir for template filters
    _outdir:str
    # Exclusive srcdir for template filters
    # Actually it is a softlink link to _outdir.
    _srcdir:str


    @classmethod
    def setup(cls, app:Sphinx):
        """You must call this method before instantiating"""
        app.connect('builder-inited', cls._on_builder_inited)
        app.connect('build-finished', cls._on_build_finished)


    @classmethod
    def _on_builder_inited(cls, app:Sphinx):
        cls._builder = app.builder
        cls._outdir = path.join(app.outdir, ANYDIR)
        ensuredir(cls._outdir)
        cls._srcdir = path.join(app.srcdir, ANYDIR)
        if path.islink(cls._srcdir):
            os.unlink(cls._srcdir)
        os.symlink(cls._outdir, cls._srcdir)


    @classmethod
    def _on_build_finished(cls, app:Sphinx, exception):
        os.unlink(cls._srcdir)


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.filters['thumbnail'] = self._thumbnail_filter
        # self.filters['watermark'] = self._watermark_filter
        self.filters['copyfile'] = self._copyfile_filter


    def _thumbnail_filter(self, imgfn:str) -> str:
        infn, outfn, relfn = self._get_in_out_rel(imgfn)
        with Image(filename=infn) as img:
            # Remove any associated profiles
            img.thumbnail()
            # If larger than 640x480, fit within box, preserving aspect ratio
            img.transform(resize='640x480>')
            img.save(filename=outfn)
        return relfn


    def _watermark_filter(self, imgfn:str) -> str:
        # TODO
        # infn, outfn, relfn = self._get_in_out_rel(imgfn)
        # with Image(filename=infn) as img:
        #     with Image(width=100, height=100,background='#0008', pseudo='caption:@SilverRainZ') as watermark:
        #         # img.watermark(watermark)
        #         watermark.save(filename=outfn)
        # return relfn
        pass


    def _copyfile_filter(self, fn:str) -> str:
        """
        Copy the file from sphinx srcdir to sphinx outdir, return the relative
        uri of current docname.
        """
        if path.isabs(fn):
            # Convert absoulte path to relative path
            fn = path.relpath(fn, '/')
        src = path.join(self._builder.srcdir, fn)
        dst = path.join(self._builder.outdir, ANYDIR, fn)
        ensuredir(path.dirname(dst))
        shutil.copy(src, dst)
        return self._relative_uri(ANYDIR, fn)


    def _relative_uri(self, *args):
        """Return a relative URL from current docname to ``*args``."""
        docname = self._builder.env.docname
        base = self._builder.get_target_uri(docname)
        return relative_uri(base, posixpath.join(*args))


    def _get_in_out_rel(self, fn:str) -> Tuple[str,str,str]:
        if path.isabs(fn):
            # Convert absoulte path to relative path
            fn = path.relpath(fn, '/')
        infn = path.join(self._builder.srcdir, fn)
        if infn.startswith(self._srcdir):
            # fn is outputted by other filters
            outfn = infn
        else:
            # fn is specified by user
            outfn = path.join(self._srcdir, fn)
            if path.isfile(outfn):
                # fn is already processed by other filters
                infn = outfn
            else:
                # Make sure output dir exists
                ensuredir(path.dirname(outfn))
        relfn = path.relpath(outfn, self._builder.srcdir)
        return (infn, outfn, relfn)

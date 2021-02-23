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

_ANYDIR = '_any'

from sphinx.util import ensuredir, relative_uri
if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.builders import Builder

import jinja2
from wand.image import Image


class Environment(jinja2.Environment):

    _builder:Builder
    # Temp directory inside source dir
    _tempdir:str
    # Softlink link to tempdir that inside sphinx srcdir
    _tempsym:str

    def __init__(self, app:Sphinx, *args, **kwargs):
        super().__init__(*args, **kwargs)
        app.connect('builder-inited', self._on_builder_inited)
        app.connect('build-finished', self._on_build_finished)

        self.filters['thumbnail'] = self._thumbnail_filter
        # self.filters['watermark'] = self._watermark_filter
        self.filters['copyfile'] = self._copyfile_filter


    def _on_builder_inited(self, app:Sphinx):
        self._builder = app.builder
        self._tempdir = tempfile.mkdtemp(prefix=_ANYDIR)
        self._tempsym = path.join(app.srcdir, _ANYDIR)
        if path.islink(self._tempsym):
            os.unlink(self._tempsym)
        os.symlink(self._tempdir, self._tempsym)


    def _on_build_finished(self, app:Sphinx, exception):
        shutil.rmtree(self._tempdir)
        os.unlink(self._tempsym)


    def _thumbnail_filter(self, imgfn:str, width:int=1280, height:int=720) -> str:
        infn, outfn, relfn = self._get_in_out_rel(imgfn)
        with Image(filename=infn) as img:
            # TODO:
            if img.width > width:
                height = int((img.height / img.width) * width)
            elif img.height > height:
                width = int((img.width / img.height) * height)
            else:
                width = img.width
                height = img.height
            img.thumbnail(width, height)
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
        src = path.join(self._builder.srcdir, fn)
        dst = path.join(self._builder.outdir, _ANYDIR, fn)
        ensuredir(path.dirname(dst))
        shutil.copy(src, dst)
        return self._relative_uri(_ANYDIR, fn)


    def _relative_uri(self, *args):
        """Return a relative URL from current docname to ``*args``."""
        docname = self._builder.env.docname
        base = self._builder.get_target_uri(docname),
        return relative_uri(base, posixpath.join(*args))


    def _get_in_out_rel(self, fn:str) -> Tuple[str,str,str]:
        infn = path.join(self._builder.srcdir, fn)
        if infn.startswith(self._tempsym):
            # fn outputted by other filters
            outfn = infn
        else:
            # fn specified by user
            outfn = path.join(self._tempsym, fn)
            if path.isfile(outfn):
                # fn is already processed by other filters
                infn = outfn
            else:
                # Make sure output dir exists
                ensuredir(path.dirname(outfn))
        relfn = path.relpath(outfn, self._builder.srcdir)
        return (infn, outfn, relfn)

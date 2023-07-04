"""
    sphinxnotes.any.template
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Jinja template extensions for sphinxnotes.any.

    :copyright: Copyright 2021 Shengyu Zhang
    :license: BSD, see LICENSE for details.
"""

from __future__ import annotations
from typing import Tuple
import os
from os import path
import posixpath
import shutil

from sphinx.util import logging
from sphinx.util.osutil import ensuredir, relative_uri
from sphinx.application import Sphinx
from sphinx.builders import Builder

import jinja2
from wand.image import Image

ANYDIR = '_any'
logger = logging.getLogger(__name__)

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

        logger.info(f'[any] exclusive srcdir: {cls._srcdir}')
        logger.info(f'[any] exclusive outdir: {cls._outdir}')

    @classmethod
    def _on_build_finished(cls, app:Sphinx, exception):
        os.unlink(cls._srcdir)


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters['thumbnail'] = self.thumbnail_filter
        self.filters['install'] = self.install_filter
        # self.filters['watermark'] = self._watermark_filter


    def thumbnail_filter(self, imgfn:str) -> str:
        imgfn = self._ensure_rel(imgfn)
        infn, outfn, relfn = self._get_in_out_rel(imgfn)

        if not self._is_outdated(outfn, infn):
            # No need to make thumbnail
            return relfn

        with Image(filename=infn) as img:
            # Remove any associated profiles
            img.thumbnail()
            # If larger than 640x480, fit within box, preserving aspect ratio
            img.transform(resize='640x480>')
            img.save(filename=outfn)
        return relfn


    def install_filter(self, fn:str) -> str:
        """
        Install file to sphinx outdir, return the relative uri of current docname.
        """

        fn = self._ensure_rel(fn)
        src = path.join(self._builder.srcdir, fn)
        target = path.join(self._builder.outdir, ANYDIR, fn)

        if not self._is_outdated(target, src):
            # No need to install file
            return relfn

        ensuredir(path.dirname(target))
        shutil.copy(src, target)
        return self._relative_uri(ANYDIR, fn)


    def watermark_filter(self, imgfn:str) -> str:
        # TODO
        # infn, outfn, relfn = self._get_in_out_rel(imgfn)
        # with Image(filename=infn) as img:
        #     with Image(width=100, height=100,background='#0008', pseudo='caption:@SilverRainZ') as watermark:
        #         # img.watermark(watermark)
        #         watermark.save(filename=outfn)
        # return relfn
        pass


    def _relative_uri(self, *args):
        """Return a relative URL from current docname to ``*args``."""
        docname = self._builder.env.docname
        base = self._builder.get_target_uri(docname)
        return relative_uri(base, posixpath.join(*args))


    def _get_in_out_rel(self, fn:str) -> Tuple[str,str,str]:
        # The pass-in filenames must be relative
        assert not path.isabs(fn)

        infn = path.join(self._builder.srcdir, fn)
        if infn.startswith(self._srcdir):
            # fn is outputted by other filters
            outfn = infn
        else:
            # fn is specified by user
            outfn = path.join(self._srcdir, fn)
            # Make sure output dir exists
            ensuredir(path.dirname(outfn))
        relfn = self._relative_uri(ANYDIR, fn)
        return (infn, outfn, relfn)


    def _ensure_rel(self, fn: str) -> str:
        """Convert site-wide absoulte path to relative path."""
        return path.relpath(fn, '/') if path.isabs(fn) else fn


    def _is_outdated(self, target:str, src: str) -> bool:
        """
        Return whether the target file is older than src file.
        The given filenames must be absoulte paths.
        """

        assert path.isabs(target)
        assert path.isabs(src)

        # If target file not found, regard as outdated
        if not path.exists(target):
            logger.debug(f'[any] {target} is outdated: not found')
            return True

        # Compare mtime
        try:
            targetmtime = path.getmtime(target)
            srcmtime = path.getmtime(src)
            outdated = srcmtime > targetmtime
            if outdated:
                logger.debug(f'[any] {target} is outdated: {srcmtime} > {targetmtime}')
        except Exception as e:
            outdated = True
            logger.debug(f'[any] {target} is outdated: {e}')
        return outdated

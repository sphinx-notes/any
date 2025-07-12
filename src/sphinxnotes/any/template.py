"""
sphinxnotes.any.template
~~~~~~~~~~~~~~~~~~~~~~~~

Jinja template extensions for sphinxnotes.any.

:copyright: Copyright 2021 Shengyu Zhang
:license: BSD, see LICENSE for details.
"""

from __future__ import annotations
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

logger = logging.getLogger(__name__)


class Environment(jinja2.Environment):
    _builder: Builder
    # Exclusive outdir for template filters
    _outdir: str
    # Exclusive srcdir for template filters
    # Actually it is a softlink link to _outdir.
    _srcdir: str
    # Same to _srcdir, but relative to Sphinx's srcdir.
    _reldir: str
    # List of user defined filter factories.
    _filter_factories = {}

    @classmethod
    def setup(cls, app: Sphinx):
        """You must call this method before instantiating"""
        app.connect('builder-inited', cls._on_builder_inited)
        app.connect('build-finished', cls._on_build_finished)

    @classmethod
    def _on_builder_inited(cls, app: Sphinx):
        cls._builder = app.builder

        # Template filters (like thumbnail_filter) may produces and new files,
        # they will be referenced in documents. While usually directive
        # (like ..image::) can only access file inside sphinx's srcdir(source/).
        #
        # So we create a dir in sphinx's outdir(_build/), and link it from srcdir,
        # then files can be referenced, then we won't messup the srcdir
        # (usually it is trakced by git), and our files can be cleaned up by
        # removing outdir.
        #
        # NOTE: we use builder name as suffix to avoid conflicts between multiple
        # builders.
        ANYDIR = '.any'
        reldir = ANYDIR + '_' + app.builder.name
        cls._outdir = path.join(app.outdir, reldir)
        cls._srcdir = path.join(app.srcdir, reldir)
        cls._reldir = path.join('/', reldir)  # abspath relatived to srcdir

        ensuredir(cls._outdir)
        # Link srcdir -> outdir when needed.
        if not path.exists(cls._srcdir):
            os.symlink(cls._outdir, cls._srcdir)
        elif not path.islink(cls._srcdir):
            os.remove(cls._srcdir)
            os.symlink(cls._outdir, cls._srcdir)

        logger.debug(f'[any] srcdir: {cls._srcdir}')
        logger.debug(f'[any] outdir: {cls._outdir}')

    @classmethod
    def add_filter(cls, name: str, ff):
        cls._filter_factories[name] = ff

    @classmethod
    def _on_build_finished(cls, app: Sphinx, exception):
        # NOTE: no need to clean up the symlink, it will cause unnecessary
        # rebuild because file is mssiing from Sphinx's srcdir. Logs like:
        #
        #   [build target] changed 'docname' missing dependency 'xxx.jpg'
        #
        # os.unlink(cls._srcdir)
        pass

    def __init__(self):
        super().__init__(
            extensions=[
                'jinja2.ext.loopcontrols',  # enable {% break %}, {% continue %}
            ]
        )

        self.filters['thumbnail'] = self.thumbnail_filter
        self.filters['install'] = self.install_filter
        # self.filters['watermark'] = self._watermark_filter
        for name, factory in self._filter_factories.items():
            self.filters[name] = factory(self._builder.env)

    def thumbnail_filter(self, imgfn: str) -> str:
        srcfn, outfn, relfn = self._get_src_out_rel(imgfn)
        if not self._is_outdated(outfn, srcfn):
            return relfn  # no need to make thumbnail
        try:
            with Image(filename=srcfn) as img:
                # Remove any associated profiles
                img.thumbnail()
                # If larger than 640x480, fit within box, preserving aspect ratio
                img.transform(resize='640x480>')
                img.save(filename=outfn)
        except Exception as e:
            logger.warning('failed to create thumbnail for %s: %s', imgfn, e)
        return relfn

    def install_filter(self, fn: str) -> str:
        """
        Install file to sphinx outdir, return the relative uri of current docname.
        """
        srcfn, outfn, relfn = self._get_src_out_rel(fn)
        if not self._is_outdated(outfn, srcfn):
            return relfn  # no need to install file
        try:
            shutil.copy(srcfn, outfn)
        except Exception as e:
            logger.warning('failed to install %s: %s', fn, e)
        return relfn

    def watermark_filter(self, imgfn: str) -> str:
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

    def _get_src_out_rel(self, fn: str) -> tuple[str, str, str]:
        """Return three paths (srcfn, outfn, relfn).
        :srcfn: abs path of fn, must inside sphinx's srcdir
        :outfn: abs path to motified file, must inside self._srcdir
        :relfn: path to outfn relatived to sphinx's srcdir
        """
        isabs = path.isabs(fn)
        if isabs:
            fn = fn[1:]  # skip os.sep so that it can be join
        else:
            docname = self._builder.env.docname
            a, b = self._builder.env.relfn2path(fn, docname)
            fn = a

        srcfn = path.join(self._builder.srcdir, fn)
        if srcfn.startswith(self._srcdir):
            # fn is outputted by other filters
            outfn = srcfn
            relfn = path.join('/', fn)
        else:
            outfn = path.join(self._srcdir, fn)  # fn is specified by user
            relfn = path.join(self._reldir, fn)
            ensuredir(path.dirname(outfn))  # make sure output dir exists
        logger.debug('[any] srcfn: %s, outfn: %s, relfn: %s', srcfn, outfn, relfn)
        return (srcfn, outfn, relfn)

    def _is_outdated(self, target: str, src: str) -> bool:
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

import os
import shutil
from osgtest.library import core
from osgtest.library import files
from osgtest.library.osgunittest import OSGTestCase
from osgtest.library import service


_NAMESPACE = "stashcache"


def _getcfg(key):
    return core.config["%s.%s" % (_NAMESPACE, key)]


def _setcfg(key, val):
    core.config["%s.%s" % (_NAMESPACE, key)] = val


class TestStopStashCache(OSGTestCase):
    @core.elrelease(7,8)
    def setUp(self):
        core.skip_ok_unless_installed("stashcache-origin-server", "stashcache-cache-server", "stashcache-client")

    def test_01_stop_origin(self):
        service.check_stop("xrootd@stashcache-origin-server")

    def test_02_stop_cache(self):
        service.check_stop("xrootd@stashcache-cache-server")

    def test_03_unconfigure(self):
        for key in [
            "cache_config_path",
            "cache_authfile_path",
            "origin_config_path",
            "caches_json_path"
        ]:
            files.restore(_getcfg(key), owner=_NAMESPACE)

    def test_04_delete_dirs(self):
        for key in ["origin_dir", "cache_dir"]:
            if os.path.isdir(_getcfg(key)):
                shutil.rmtree(_getcfg(key))

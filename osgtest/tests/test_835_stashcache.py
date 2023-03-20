import os
import shutil
from osgtest.library import core
from osgtest.library import files
from osgtest.library.osgunittest import OSGTestCase
from osgtest.library import service


NAMESPACE = "stashcache"


def getcfg(key):
    return core.config["%s.%s" % (NAMESPACE, key)]


def stop_xrootd(instance):
    svc = "xrootd@%s" % instance
    service.check_stop(svc)


class TestStopStashCache(OSGTestCase):
    def setUp(self):
        core.skip_ok_unless_installed("stash-origin",
                                      "stash-cache",
                                      "stashcache-client",
                                      by_dependency=True)

    def test_01_stop_stash_origin(self):
        stop_xrootd("stash-origin")

    def test_02_stop_stash_origin_auth(self):
        stop_xrootd("stash-origin-auth")

    def test_03_stop_stash_cache(self):
        stop_xrootd("stash-cache")

    def test_04_stop_stash_cache_auth(self):
        stop_xrootd("stash-cache-auth")

    def test_05_unconfigure(self):
        for path in getcfg("filelist"):
            files.restore(path, owner=NAMESPACE)

    def test_06_delete_dirs(self):
        for key in ["OriginRootdir", "CacheRootdir"]:
            if os.path.isdir(getcfg(key)):
                shutil.rmtree(getcfg(key))

    def test_07_remove_certs(self):
        # Do the keys first, so that the directories will be empty for the certs.
        core.remove_cert('certs.xrootdkey')
        core.remove_cert('certs.xrootdcert')

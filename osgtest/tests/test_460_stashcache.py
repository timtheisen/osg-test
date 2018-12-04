import os
import pwd
import random
import tempfile

from osgtest.library import core
from osgtest.library import files
from osgtest.library.osgunittest import OSGTestCase
from osgtest.library import service
try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen


_NAMESPACE = "stashcache"

def _getcfg(key):
    return core.config["%s.%s" % (_NAMESPACE, key)]

def _setcfg(key, val):
    core.config["%s.%s" % (_NAMESPACE, key)] = val


class TestStashCache(OSGTestCase):
    # testfiles with random contents
    testfiles = [
        ("testfile%d" % x, str(random.random()))
        for x in range(4)
    ]

    def assertCached(self, name, contents):
        fpath = os.path.join(_getcfg("cache_dir"), name)
        self.assertTrue(os.path.exists(fpath),
                        name + " not cached")
        self.assertEqual(contents, files.read(fpath, as_single_string=True),
                         "cached file %s contents do not match expected" % name)

    @core.elrelease(7,8)
    def setUp(self):
        core.skip_ok_unless_installed("stashcache-origin-server", "stashcache-cache-server", "stashcache-client")
        self.skip_bad_unless(service.is_running("xrootd@stashcache-origin-server"))
        self.skip_bad_unless(service.is_running("xrootd@stashcache-cache-server"))

    def test_01_create_files(self):
        xrootd_user = pwd.getpwnam("xrootd")
        for name, contents in self.testfiles:
            files.write(os.path.join(_getcfg("origin_dir"), name),
                        contents, backup=False, chmod=0o644,
                        chown=(xrootd_user.pw_uid, xrootd_user.pw_gid))

    def test_02_xroot_fetch_from_origin(self):
        name, contents = self.testfiles[0]
        result, _, _ = \
            core.check_system(["xrdcp", "-d1", "-N", "-f",
                               "root://localhost:%d//%s" % (_getcfg("origin_xroot_port"), name),
                               "-"], "Checking xroot copy from origin")
        self.assertEqual(result, contents, "downloaded file does not match expected")

    def test_03_http_fetch_from_cache(self):
        name, contents = self.testfiles[1]
        try:
            f = urlopen(
                "http://localhost:%d/%s" % (_getcfg("cache_http_port"), name)
            )
            result = f.read()
        except IOError as e:
            self.fail("Unable to download from cache via http: %s" % e)
        self.assertEqual(result, contents, "downloaded file does not match expected")
        self.assertCached(name, contents)

    def test_04_xroot_fetch_from_cache(self):
        name, contents = self.testfiles[2]
        result, _, _ = \
            core.check_system(["xrdcp", "-d1", "-N", "-f",
                               "root://localhost:%d//%s" % (_getcfg("cache_xroot_port"), name),
                               "-"], "Checking xroot copy from cache")
        self.assertEqual(result, contents, "downloaded file does not match expected")
        self.assertCached(name, contents)

    def test_05_stashcp(self):
        name, contents = self.testfiles[3]
        with tempfile.NamedTemporaryFile(mode="r+b") as tf:
            core.check_system(["stashcp", "-d", "/"+name, tf.name],
                              "Checking stashcp")
            result = tf.read()
        self.assertEqual(result, contents, "stashcp'ed file does match expected")
        self.assertCached(name, contents)

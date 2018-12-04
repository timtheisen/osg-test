import os
import pwd

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
    _text = "this is a test"

    @core.elrelease(7,8)
    def setUp(self):
        core.skip_ok_unless_installed("stashcache-origin-server", "stashcache-cache-server", "stashcache-client")
        self.skip_bad_unless(service.is_running("xrootd@stashcache-origin-server"))
        self.skip_bad_unless(service.is_running("xrootd@stashcache-cache-server"))

    def test_01_create_file(self):
        xrootd_user = pwd.getpwnam("xrootd")
        files.write(os.path.join(_getcfg("origin_dir"), "testfile"),
                    self._text, backup=False, chmod=0o644,
                    chown=(xrootd_user.pw_uid, xrootd_user.pw_gid))

    def test_02_fetch_from_origin(self):
        result, _, _ = \
            core.check_system(["xrdcp", "-d1", "-N", "-f",
                               "root://localhost:%d//testfile" % _getcfg("origin_port"),
                               "-"], "Checking xroot copy from origin")
        self.assertEqual(result, self._text, "downloaded file does not match expected")

    def test_03_http_fetch_from_cache(self):
        try:
            f = urlopen(
                "http://localhost:%d/testfile" % _getcfg("cache_http_port")
            )
            result = f.read()
        except IOError as e:
            self.fail("Unable to download from cache via http: %s" % e)
        self.assertEqual(result, self._text, "downloaded file does not match expected")
        self.assertTrue(os.path.exists(os.path.join(_getcfg("cache_dir"), "testfile")),
                        "testfile not cached")

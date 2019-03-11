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


NAMESPACE = "stashcache"

def getcfg(key):
    return core.config["%s.%s" % (NAMESPACE, key)]


# TODO Work with authed origin/cache as well.  A separate class would probably be the best.
class TestStashCache(OSGTestCase):
    # testfiles with random contents
    testfiles = [
        ("testfile%d" % x, str(random.random()))
        for x in range(4)
    ]

    def assertCached(self, name, contents):
        fpath = os.path.join(getcfg("CacheRootdir"), getcfg("OriginExport").lstrip("/"), name)
        self.assertTrue(os.path.exists(fpath),
                        name + " not cached")
        self.assertEqualVerbose(actual=files.read(fpath, as_single_string=True),
                                expected=contents,
                                message="cached file %s mismatch" % name)

    def skip_bad_unless_running(self, *services):
        for svc in services:
            self.skip_bad_unless(service.is_running(svc), "%s not running" % svc)

    @core.elrelease(7,8)
    def setUp(self):
        core.skip_ok_unless_installed("stash-origin",
                                      "stash-cache",
                                      "stashcache-client",
                                      by_dependency=True)
        self.skip_ok_if(core.PackageVersion("xcache") < "1.0.2")
        self.skip_bad_unless_running("xrootd@stash-origin", "xrootd@stash-cache")

    def test_01_create_files(self):
        xrootd_user = pwd.getpwnam("xrootd")
        for name, contents in self.testfiles:
            files.write(os.path.join(getcfg("OriginRootdir"), getcfg("OriginExport").lstrip("/"), name),
                        contents, backup=False, chmod=0o644,
                        chown=(xrootd_user.pw_uid, xrootd_user.pw_gid))

    def test_02_xroot_fetch_from_origin(self):
        name, contents = self.testfiles[0]
        path = os.path.join(getcfg("OriginExport"), name)
        result, _, _ = \
            core.check_system(["xrdcp", "-d1", "-N", "-f",
                               "root://localhost:%d/%s" % (getcfg("OriginXrootPort"), path),
                               "-"], "Checking xroot copy from origin")
        self.assertEqualVerbose(result, contents, "downloaded file mismatch")

    def test_03_http_fetch_from_cache(self):
        name, contents = self.testfiles[1]
        path = os.path.join(getcfg("OriginExport"), name)
        try:
            f = urlopen(
                "http://localhost:%d/%s" % (getcfg("CacheHTTPPort"), path)
            )
            result = f.read()
        except IOError as e:
            self.fail("Unable to download from cache via http: %s" % e)
        self.assertEqualVerbose(result, contents, "downloaded file mismatch")
        self.assertCached(name, contents)

    def test_04_xroot_fetch_from_cache(self):
        name, contents = self.testfiles[2]
        path = os.path.join(getcfg("OriginExport"), name)
        result, _, _ = \
            core.check_system(["xrdcp", "-d1", "-N", "-f",
                               "root://localhost:%d/%s" % (getcfg("CacheXrootPort"), path),
                               "-"], "Checking xroot copy from cache")
        self.assertEqualVerbose(result, contents, "downloaded file mismatch")
        self.assertCached(name, contents)

    def test_05_stashcp(self):
        command = ["stashcp", "-d"]
        if core.PackageVersion('stashcache-client') < '5.1.0-5':
            command.append("--cache=root://localhost")
        name, contents = self.testfiles[3]
        path = os.path.join(getcfg("OriginExport"), name)
        with tempfile.NamedTemporaryFile(mode="r+b") as tf:
            core.check_system(command + [path, tf.name],
                              "Checking stashcp")
            result = tf.read()
        self.assertEqualVerbose(result, contents, "stashcp'ed file mismatch")
        self.assertCached(name, contents)

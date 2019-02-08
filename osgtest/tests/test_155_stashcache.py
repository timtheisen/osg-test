import os
import pwd

from osgtest.library import core
from osgtest.library import files
from osgtest.library.osgunittest import OSGTestCase
from osgtest.library import service


CACHE_DIR = "/tmp/sccache"
CACHE_XROOT_PORT = 1094  # can't change this - stashcp doesn't allow you to specify port
CACHE_HTTP_PORT = 8001
ORIGIN_XROOT_PORT = 1095
ORIGIN_DIR = "/tmp/scorigin"
CACHE_AUTHFILE_PATH = "/etc/xrootd/Authfile-cache"
CACHE_CONFIG_PATH = "/etc/xrootd/xrootd-stashcache-cache-server.cfg"
ORIGIN_CONFIG_PATH = "/etc/xrootd/xrootd-stashcache-origin-server.cfg"
CACHES_JSON_PATH = "/etc/stashcache/caches.json"


# TODO Set up authenticated stashcache as well
CACHE_CONFIG_TEXT = """\
all.export  /
set cachedir = {CACHE_DIR}
xrd.allow host *
sec.protocol  host
all.adminpath /var/spool/xrootd

xrootd.trace emsg login stall redirect
ofs.trace all
xrd.trace all
cms.trace all

ofs.osslib  libXrdPss.so
# normally this is the redirector but we don't have one in this environment
pss.origin localhost:{ORIGIN_XROOT_PORT}
pss.cachelib libXrdFileCache.so
pss.setopt DebugLevel 1

oss.localroot $(cachedir)

pfc.blocksize 512k
pfc.ram       1024m
# ^ xrootd won't start without a gig
pfc.prefetch  10
pfc.diskusage 0.90 0.95

ofs.authorize 1
acc.audit deny grant

acc.authdb {CACHE_AUTHFILE_PATH}
sec.protbind * none
xrd.protocol http:{CACHE_HTTP_PORT} libXrdHttp.so

xrd.port {CACHE_XROOT_PORT}

http.listingdeny yes
http.staticpreload http://static/robots.txt /etc/xrootd/stashcache-robots.txt

# Tune the client timeouts to more aggressively timeout.
pss.setopt ParallelEvtLoop 10
pss.setopt RequestTimeout 25
#pss.setopt TimeoutResolution 1
pss.setopt ConnectTimeout 25
pss.setopt ConnectionRetry 2
#pss.setopt StreamTimeout 35

all.sitename osgtest

xrootd.diglib * /etc/xrootd/digauth.cf
""".format(**globals())


CACHE_AUTHFILE_TEXT = """\
u * / rl
"""


ORIGIN_CONFIG_TEXT = """\
xrd.allow host *
sec.protocol  host
sec.protbind  * none
all.adminpath /var/spool/xrootd
all.pidpath /var/run/xrootd

# The directory on local disk containing the files to share, e.g. "/stash".
oss.localroot {ORIGIN_DIR}
all.export /

xrd.port {ORIGIN_XROOT_PORT}
all.role server

xrootd.trace emsg login stall redirect
ofs.trace all
xrd.trace all
cms.trace all
""".format(**globals())


CACHES_JSON_TEXT = """\
[
{"name":"root://localhost", "status":1, "longitude":-89.4012, "latitude":43.0731}
]
"""


_NAMESPACE = "stashcache"


def _getcfg(key):
    return core.config["%s.%s" % (_NAMESPACE, key)]


def _setcfg(key, val):
    core.config["%s.%s" % (_NAMESPACE, key)] = val


class TestStartStashCache(OSGTestCase):
    @core.elrelease(7,8)
    def setUp(self):
        core.skip_ok_unless_installed("stashcache-origin-server",
                                      "stashcache-cache-server",
                                      "stashcache-client",
                                      by_dependency=True)

    def test_01_configure(self):
        for key, val in [
            ("cache_authfile_path", CACHE_AUTHFILE_PATH),
            ("cache_config_path", CACHE_CONFIG_PATH),
            ("origin_config_path", ORIGIN_CONFIG_PATH),
            ("caches_json_path", CACHES_JSON_PATH),
            ("cache_http_port", CACHE_HTTP_PORT),
            ("origin_dir", ORIGIN_DIR),
            ("cache_dir", CACHE_DIR),
            ("origin_xroot_port", ORIGIN_XROOT_PORT),
            ("cache_xroot_port", CACHE_XROOT_PORT)
        ]:
            _setcfg(key, val)

        xrootd_user = pwd.getpwnam("xrootd")
        for d in [_getcfg("origin_dir"), _getcfg("cache_dir"),
                  os.path.dirname(_getcfg("caches_json_path"))]:
            files.safe_makedirs(d)
            os.chown(d, xrootd_user.pw_uid, xrootd_user.pw_gid)

        for key, text in [
            ("cache_config_path", CACHE_CONFIG_TEXT),
            ("cache_authfile_path", CACHE_AUTHFILE_TEXT),
            ("origin_config_path", ORIGIN_CONFIG_TEXT),
            ("caches_json_path", CACHES_JSON_TEXT)
        ]:
            files.write(_getcfg(key), text, owner=_NAMESPACE, chmod=0o644)

    def test_02_start_origin(self):
        if not service.is_running("xrootd@stashcache-origin-server"):
            service.check_start("xrootd@stashcache-origin-server")

    def test_03_start_cache(self):
        if not service.is_running("xrootd@stashcache-cache-server"):
            service.check_start("xrootd@stashcache-cache-server")

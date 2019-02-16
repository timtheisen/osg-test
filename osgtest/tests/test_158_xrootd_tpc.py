import os
import pwd
import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.service as service
import osgtest.library.osgunittest as osgunittest


HTTP_PORT1 = 9001  # chosen so it doesn't conflict w/ the stashcache instances
HTTP_PORT2 = 9002

XROOTD_CFG_TEXT = """\
cms.space min 2g 5g
xrootd.seclib /usr/lib64/libXrdSec-4.so
sec.protocol /usr/lib64 gsi -certdir:/etc/grid-security/certificates \
    -cert:/etc/grid-security/xrd/xrdcert.pem \
    -key:/etc/grid-security/xrd/xrdkey.pem \
    -crl:3 \
    --gmapopt:10 \
    --gmapto:0 \
    %s

acc.authdb /etc/xrootd/auth_file
ofs.authorize

if exec xrootd
  http.cadir /etc/grid-security/certificates
  http.cert /etc/grid-security/xrd/xrdcert.pem
  http.key /etc/grid-security/xrd/xrdkey.pem
  http.listingdeny yes
  http.desthttps yes
  http.trace all debug
  # Enable third-party-copy
  http.exthandler xrdtpc libXrdHttpTPC.so
  # Pass the bearer token to the Xrootd authorization framework.
  http.header2cgi Authorization authz

  # Enable Macaroons
  ofs.authlib libXrdMacaroons.so libXrdAccSciTokens.so
  xrd.port %d
  xrd.protocol http:%d /usr/lib64/libXrdHttp-4.so
fi
http.exthandler xrdmacaroons libXrdMacaroons.so
all.sitename VDTTESTSITE

"""

class TestStartXrootdTPC(osgunittest.OSGTestCase):
    @core.elrelease(7,8)
    def test_01_configure_xrootd(self):
        core.config['xrootd.tpc.config-1'] = '/etc/xrootd/xrootd-third-party-copy-1.cfg'
        core.config['xrootd.tpc.config-2'] = '/etc/xrootd/xrootd-third-party-copy-2.cfg'
        core.config['xrootd.tpc.http-port1'] = HTTP_PORT1
        core.config['xrootd.tpc.http-port2'] = HTTP_PORT2
        core.state['xrootd.started-http-server-1'] = False
        core.state['xrootd.started-http-server-2'] = False
        core.state['xrootd.tpc.backups-exist'] = False

        self.skip_ok_unless(core.options.adduser, 'user not created')
        core.skip_ok_unless_installed('xrootd', 'xrootd-scitokens', by_dependency=True)

        user = pwd.getpwnam("xrootd")
        core.skip_ok_unless_installed('globus-proxy-utils')

        lcmaps_packages = ('lcmaps', 'lcmaps-db-templates', 'xrootd-lcmaps', 'vo-client', 'vo-client-lcmaps-voms')
        if all([core.rpm_is_installed(x) for x in lcmaps_packages]):
            core.log_message("Using xrootd-lcmaps authentication")
            sec_protocol = '-authzfun:libXrdLcmaps.so -authzfunparms:--loglevel,5'
            #XROOTD_CFG_TEXT += "http.secxtractor /usr/lib64/libXrdLcmaps.so/n"
            sec_protocol += ',--policy,authorize_only'
        else:
            core.log_message("Using XRootD mapfile authentication")
            sec_protocol = '-gridmap:/etc/grid-security/xrd/xrdmapfile'

        files.write(core.config['xrootd.tpc.config-1'],
                     XROOTD_CFG_TEXT % (sec_protocol, core.config['xrootd.tpc.http-port1'], core.config['xrootd.tpc.http-port1']),
                     owner='xrootd', backup=True, chown=(user.pw_uid, user.pw_gid))
        files.write(core.config['xrootd.tpc.config-2'],
                     XROOTD_CFG_TEXT % (sec_protocol, core.config['xrootd.tpc.http-port2'], core.config['xrootd.tpc.http-port1']),
                     owner='xrootd', backup=True, chown=(user.pw_uid, user.pw_gid))
        core.state['xrootd.tpc.backups-exist'] = True
 
    def test_02_create_secrets(self):
        core.skip_ok_unless_installed('xrootd', 'xrootd-scitokens', by_dependency=True)
        core.config['xrootd.tpc.macaroon-secret-1'] = '/etc/xrootd/macaroon-secret-1'
        core.config['xrootd.tpc.macaroon-secret-2'] = '/etc/xrootd/macaroon-secret-2'
        core.check_system(["openssl", "rand", "-base64", "-out",
                               core.config['xrootd.tpc.macaroon-secret-1'], "64"], "Creating simmetric key")
        core.check_system(["openssl", "rand", "-base64", "-out",
                               core.config['xrootd.tpc.macaroon-secret-2'], "64"], "Creating simmetric key")
        files.append(core.config['xrootd.tpc.config-1'], 
                         "macaroons.secretkey %s"%(core.config['xrootd.tpc.macaroon-secret-1']),
                         owner='xrootd', backup=False)
        files.append(core.config['xrootd.tpc.config-2'],
                         "macaroons.secretkey %s"%(core.config['xrootd.tpc.macaroon-secret-2']),
                      owner='xrootd', backup=False)


    def test_03_start_xrootd(self):
        core.skip_ok_unless_installed('xrootd', 'xrootd-scitokens', by_dependency=True)
        core.config['xrootd_tpc_service_1'] = "xrootd@third-party-copy-1"
        core.config['xrootd_tpc_service_2'] = "xrootd@third-party-copy-2"
        service.check_start(core.config['xrootd_tpc_service_1'], logToCheck = '/var/log/xrootd/third-party-copy-1/xrootd.log')
        service.check_start(core.config['xrootd_tpc_service_2'], logToCheck = '/var/log/xrootd/third-party-copy-2/xrootd.log')
        core.state['xrootd.started-http-server-1'] = True
        core.state['xrootd.started-http-server-2'] = True


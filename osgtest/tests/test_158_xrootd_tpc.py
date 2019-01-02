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
  http.secxtractor /usr/lib64/libXrdLcmaps.so
  http.listingdeny yes
  http.desthttps yes

  # Enable third-party-copy
  http.exthandler xrdtpc libXrdHttpTPC.so
  # Pass the bearer token to the Xrootd authorization framework.
  http.header2cgi Authorization authz

  # Enable Macaroons
  ofs.authlib libXrdMacaroons.so libXrdAccSciTokens.so

fi

if named xrd-TPC-1
  xrd.protocol http:%d /usr/lib64/libXrdHttp-4.so
fi

if named xrd-TPC-2
  xrd.protocol http:%d /usr/lib64/libXrdHttp-4.so
fi
end
"""

class TestStartXrootdTPC(osgunittest.OSGTestCase):
    @core.elrelease(7,8)
    def test_01_start_xrootd(self):
        core.config['certs.xrootdcert'] = '/etc/grid-security/xrd/xrdcert.pem'
        core.config['certs.xrootdkey'] = '/etc/grid-security/xrd/xrdkey.pem'
        core.config['xrootd.tpc.config'] = '/etc/xrootd/xrootd-third-party-copy.cfg'
        core.config['xrootd.tpc.http-port1'] = HTTP_PORT1
        core.config['xrootd.tpc.http-port2'] = HTTP_PORT2
        core.state['xrootd.started-http-server-1'] = False
        core.state['xrootd.started-http-server-2'] = False
        core.state['xrootd.tpc.backups-exist'] = False

        self.skip_ok_unless(core.options.adduser, 'user not created')
        core.skip_ok_unless_installed('xrootd', by_dependency=True)

        user = pwd.getpwnam("xrootd")
        core.skip_ok_unless_installed('globus-proxy-utils')

        lcmaps_packages = ('lcmaps', 'lcmaps-db-templates', 'xrootd-lcmaps', 'vo-client', 'vo-client-lcmaps-voms')
        if all([core.rpm_is_installed(x) for x in lcmaps_packages]):
            core.log_message("Using xrootd-lcmaps authentication")
            sec_protocol = '-authzfun:libXrdLcmaps.so -authzfunparms:--loglevel,5'
            if core.PackageVersion('xrootd-lcmaps') >= '1.4.0':
                sec_protocol += ',--policy,authorize_only'
        else:
            core.log_message("Using XRootD mapfile authentication")
            sec_protocol = '-gridmap:/etc/grid-security/xrd/xrdmapfile'

        files.append(core.config['xrootd.tpc.config'],
                     XROOTD_CFG_TEXT % (sec_protocol, core.config['xrootd.port']),
                     owner='xrootd', backup=True)
        core.state['xrootd.tpc.backups-exist'] = True

    def test_02_start_xrootd(self):
        core.skip_ok_unless_installed('xrootd', 'xrootd-scitokens', by_dependency=True)
        core.config['xrootd_tpc_service_1'] = "xrd-TPC-1@third-party-copy"
        core.config['xrootd_tpc_service_2'] = "xrd-TPC-2@third-party-copy"
        service.check_start(core.config['xrootd_tpc_service_1'])
        service.check_start(core.config['xrootd_tpc_service_2'])
        
        core.state['xrootd_tpc_service_1'] = True
        core.state['xrootd_tpc_service_2'] = True

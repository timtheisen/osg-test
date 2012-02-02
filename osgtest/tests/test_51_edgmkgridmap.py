import os
import osgtest.library.core as core
import osgtest.library.files as files
import pwd
import socket
import unittest

class TestEdgMkGridmap(unittest.TestCase):

    def test_01_config_mkgridmap(self):
        core.config['edg.conf'] = '/usr/share/osg-test/edg-mkgridmap.conf'

        if core.missing_rpm('edg-mkgridmap', 'voms-server'):
            return

        files.write(core.config['edg.conf'],
                    ('group vomss://%s:8443/voms/%s %s\n' %
                     (socket.getfqdn(), core.config['voms.vo'],
                      core.options.username)))
        core.system(('cat', core.config['edg.conf']))

    def test_02_edg_mkgridmap(self):
        if core.missing_rpm('edg-mkgridmap', 'voms-server'):
            return

        command = ('edg-mkgridmap', '--conf', core.config['edg.conf'])
        os.environ['GRIDMAP'] = '/usr/share/osg-test/grid-mapfile'
        os.environ['USER_VO_MAP'] = '/usr/share/osg-test/user-vo-map'
        os.environ['EDG_MKGRIDMAP_LOG'] = \
            '/usr/share/osg-test/edg-mkgridmap.log'
        os.environ['VO_LIST_FILE'] = '/usr/share/osg-test/vo-list-file'
        os.environ['UNDEFINED_ACCTS_FILE'] = '/usr/share/osg-test/undef-ids'
        core.check_system(command, 'Run edg-mkgridmap')

        pwd_entry = pwd.getpwnam(core.options.username)
        cert_path = os.path.join(pwd_entry.pw_dir, '.globus', 'usercert.pem')
        user_cert_dn, user_cert_issuer = core.certificate_info(cert_path)
        expected = '"%s" %s' % (user_cert_dn, core.options.username)

        contents = files.read(os.environ['GRIDMAP'], True)
        self.assert_(expected in contents, 'Expected grid-mapfile contents')

    def test_03_clean_edg_mkgridmap(self):
        if core.missing_rpm('edg-mkgridmap', 'voms-server'):
            return

        for envvar in ('VO_LIST_FILE', 'UNDEFINED_ACCTS_FILE',
                       'EDG_MKGRIDMAP_LOG', 'USER_VO_MAP', 'GRIDMAP'):
            files.remove(os.environ[envvar])
            del os.environ[envvar]
        files.restore(core.config['edg.conf'])

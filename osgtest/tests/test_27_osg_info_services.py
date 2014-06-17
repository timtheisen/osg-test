import os
import socket
import stat
import unittest
import tempfile

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.tomcat as tomcat
import osgtest.library.osgunittest as osgunittest
import osgtest.library.certificates as certs

class TestStartOSGInfoServices(osgunittest.OSGTestCase):

    #possible_rpms = ['osg-ce-condor',
    #                 'osg-ce-pbs',
    #                 'osg-ce-lsf',]
    possible_rpms = ['osg-ce',
                     'htcondor-ce']

    def test_01_config_certs(self):
        #core.skip_ok_unles_installed('osg-ce')
        core.skip_ok_unless_one_installed(*self.possible_rpms)
        core.config['certs.hostcert'] = '/etc/grid-security/hostcert.pem'
        core.config['certs.hostkey'] = '/etc/grid-security/hostkey.pem'
        core.config['certs.httpcert'] = '/etc/grid-security/http/httpcert.pem'
        core.config['certs.httpkey'] = '/etc/grid-security/http/httpkey.pem'
        
    def test_02_install_http_certs(self):
        core.skip_ok_unless_one_installed(*self.possible_rpms)
        httpcert = core.config['certs.httpcert']
        httpkey = core.config['certs.httpkey']
        self.skip_ok_if(core.check_file_and_perms(httpcert, 'tomcat', 0644) and
                        core.check_file_and_perms(httpkey, 'tomcat', 0400),
                        'HTTP cert exists and has proper permissions')
        certs.install_cert('certs.httpcert', 'certs.hostcert', 'tomcat', 0644)
        certs.install_cert('certs.httpkey', 'certs.hostkey', 'tomcat', 0400)

    def test_03_create_app_dir_structure(self):
        core.skip_ok_unless_one_installed(*self.possible_rpms)
        temp_dir = tempfile.mkdtemp(suffix = 'osg-info-services')
        core.config['osg-info-services.tmp-dir-suffix'] = temp_dir
        os.mkdir(temp_dir + '/osg')
        os.mkdir(temp_dir + '/osg/app_dir')
        os.mkdir(temp_dir + '/osg/app_dir/etc')
        os.mkdir(temp_dir + '/osg/data_dir')

    def test_04_config_storage_file(self):
        core.skip_ok_unless_one_installed(*self.possible_rpms)
        core.config['osg-info-services.storage-file'] = '/etc/osg/config.d/10-storage.ini'
        temp_dir = core.config['osg-info-services.tmp-dir-suffix']
        files.replace_regexpr(core.config['osg-info-services.storage-file'],
                      'app_dir = *',
                      'app_dir = ' + temp_dir + '/osg/app_dir',
                      owner = 'root')
        files.replace_regexpr(core.config['osg-info-services.storage-file'],
                      'data_dir = *',
                      'data_dir = ' + temp_dir + '/osg/data_dir', 
                      backup = False)
        

    def test_05_config_squid_file(self):
        core.skip_ok_unless_one_installed(*self.possible_rpms)
        core.config['osg-info-services.squid-file'] = '/etc/osg/config.d/01-squid.ini'
        files.replace_regexpr(core.config['osg-info-services.squid-file'],
                      'location = *',
                      'location = UNAVAILABLE',
                      owner = 'root')

    def test_06_config_misc_file(self):
        core.skip_ok_unless_one_installed(*self.possible_rpms)
        core.config['osg-info-services.misc-file'] = '/etc/osg/config.d/10-misc.ini'
        files.replace(core.config['osg-info-services.misc-file'],
                      'gums_host = DEFAULT',
                      'gums_host = itb-gums-rsv.chtc.wisc.edu',
                      owner = 'root')
        
    def test_07_config_gip_file(self):
        core.skip_ok_unless_one_installed(*self.possible_rpms)
        core.config['osg-info-services.gip-file'] = '/etc/osg/config.d/30-gip.ini'
        files.append(core.config['osg-info-services.gip-file'],
                     "[Subcluster fermicloud osg test]\n",
                     owner = 'root')
        files.append(core.config['osg-info-services.gip-file'],
                     "name = fermicloud osg test\n",
                     backup = False) 
        files.append(core.config['osg-info-services.gip-file'],
                     "node_count = 1\n",
                     backup = False)
        files.append(core.config['osg-info-services.gip-file'],
                     "ram_mb = 4110\n",
                     backup = False)
        files.append(core.config['osg-info-services.gip-file'],
                     "swap_mb = 4000\n",
                     backup = False)
        files.append(core.config['osg-info-services.gip-file'],
                     "cpu_model = Dual-Core AMD Opteron(tm) Processor 2216\n",
                     backup = False)
        files.append(core.config['osg-info-services.gip-file'],
                     "cpu_vendor = AMD\n",
                     backup = False)
        files.append(core.config['osg-info-services.gip-file'],
                     "cpu_speed_mhz = 2400\n",
                     backup = False)
        files.append(core.config['osg-info-services.gip-file'],
                     "cpus_per_node = 2\n",
                     backup = False)
        files.append(core.config['osg-info-services.gip-file'],
                     "cores_per_node = 2\n",
                     backup = False)
        files.append(core.config['osg-info-services.gip-file'],
                     "inbound_network = FALSE\n",
                     backup = False)
        files.append(core.config['osg-info-services.gip-file'],
                     "outbound_network = TRUE\n",
                     backup = False)
        files.append(core.config['osg-info-services.gip-file'],
                     "cpu_platform = x86_64\n",
                     backup = False)
    
    def test_08_config_site_info_file(self):
        core.skip_ok_unless_one_installed(*self.possible_rpms)
        core.config['osg-info-services.siteinfo-file'] = '/etc/osg/config.d/40-siteinfo.ini'
        files.replace(core.config['osg-info-services.siteinfo-file'],
                      'group = OSG',
                      'group = OSG-ITB',
                      owner = 'root')
        files.replace_regexpr(core.config['osg-info-services.siteinfo-file'],
                      'host_name = *',
                      'host_name = ' + core.get_hostname(),
                      backup = False)
        files.replace(core.config['osg-info-services.siteinfo-file'],
                      'sponsor = UNAVAILABLE',
                      'sponsor = mis:100',
                      backup = False)
        files.replace(core.config['osg-info-services.siteinfo-file'],
                      'contact = UNAVAILABLE',
                      'contact = Lando Calrissian',
                      backup = False)
        files.replace(core.config['osg-info-services.siteinfo-file'],
                      'email = UNAVAILABLE',
                      'email = lcalrissian@milleniumfalcon.com',
                      backup = False)
        files.replace(core.config['osg-info-services.siteinfo-file'],
                      'city = UNAVAILABLE',
                      'city = Cloud City',
                      backup = False)
        files.replace(core.config['osg-info-services.siteinfo-file'],
                      'country = UNAVAILABLE',
                      'country = Bespin',
                      backup = False)
        files.replace_regexpr(core.config['osg-info-services.siteinfo-file'], 
                      'longitude =*', 
                      'longitude = -1',
                      backup = False)
        files.replace(core.config['osg-info-services.siteinfo-file'],
                      'latitude = UNAVAILABLE',
                      'latitude = 45',
                      backup = False)
        
    def test_09_config_user_vo_map(self):
        # Configurations for the user_vo_map
        core.skip_ok_unless_one_installed(*self.possible_rpms)
        core.config['osg-info-services.user-vo-map'] = '/var/lib/osg/user-vo-map'
        files.append(core.config['osg-info-services.user-vo-map'],
                     core.options.username + ' mis',
                     owner = 'root')
                     
    def test_10_config_condor(self):
        # Configurations needed if bath system is condor.
        core.skip_ok_unless_installed('osg-ce-condor')
        core.config['osg-info-services.condor-file'] = '/etc/osg/config.d/20-condor.ini'
        files.replace_regexpr(core.config['osg-info-services.condor-file'],
                      'enabled = *',
                      'enabled = True',
                      owner = 'root')
        files.replace_regexpr(core.config['osg-info-services.gip-file'],
                      'batch = *',
                      'batch = condor',
                      backup = False)
        
    def test_11_config_pbs(self):
        # Configuration needed if batch system is pbs
        core.skip_ok_unless_installed('osg-ce-pbs')
        core.config['osg-info-services.pbs-file'] = '/etc/osg/config.d/20-pbs.ini'
        files.replace_regexpr(core.config['osg-info-services.pbs-file'],
                      'enabled = *',
                      'enabled = True',
                      owner = 'root')
        files.replace_regexpr(core.config['osg-info-services.gip-file'],
                      'batch = *',
                      'batch = pbs',
                      backup = False)

    def test_12_config_lsf(self):
        # Configuration needed if batch system is lsf                                                                                          
        core.skip_ok_unless_installed('osg-ce-lsf')
        core.config['osg-info-services.lsf-file'] = '/etc/osg/config.d/20-lsf.ini'
        files.replace_regexpr(core.config['osg-info-services.lsf-file'],
                      'enabled = *',
                      'enabled = True',
                      owner = 'root')
        files.replace_regexpr(core.config['osg-info-services.gip-file'],
                      'batch = *',
                      'batch = lsf',
                      backup = False)

    def test_13_config_sge(self):
        # Configuration needed if batch system is sge                                                                                          
        core.skip_ok_unless_installed('osg-ce-sge')
        core.config['osg-info-services.sge-file'] = '/etc/osg/config.d/20-sge.ini'
        files.replace_regexpr(core.config['osg-info-services.sge-file'],
                      'enabled = *',
                      'enabled = True',
                      owner = 'root')
        files.replace_regexpr(core.config['osg-info-services.sge-file'],
                      'sge_root = *',
                      'sge_root = /usr/share/gridengine',
                      backup = False)
        os.environ['SGE_ROOT'] = '/usr/share/gridengine'
        files.replace_regexpr(core.config['osg-info-services.sge-file'],
                      'sge_bin_location = *',
                      'sge_bin_location = /usr/share/gridengine/bin',
                      backup = False)
        files.replace_regexpr(core.config['osg-info-services.gip-file'],
                      'batch = *',
                      'batch = sge',
                      backup = False)

    def test_14_config_gram_gateway(self):
        core.skip_ok_unless_installed('osg-ce')
        core.config['osg-info-services.gateway-file'] = '/etc/osg/config.d/10-gateway.ini'
        files.replace_regexpr(core.config['osg-info-services.gateway-file'],
                      'gram_gateway_enabled = *',
                      'gram_gateway_enabled = True',
                      owner = 'root')

    def test_15_config_htcondor_gateway(self):
        core.skip_ok_unless_installed('htcondor-ce')
        core.config['osg-info-services.gateway-file'] ='/etc/osg/config.d/10-gateway.ini'
        files.replace_regexpr(core.config['osg-info-services.gateway-file'],
                      'htcondor_gateway_enabled = *',
                      'htcondor_gateway_enabled = True',
                      owner = 'root')

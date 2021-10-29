from urllib import error

from ..library import core, credentials, osgunittest


class TestTokens(osgunittest.OSGTestCase):
    def test_00_setup(self):
        for token_name in ["condor_write", "xrootd", "xrootd_tpc_1", "xrootd_tpc_2"]:
            credentials.reserve_scitoken(token_name)

    def test_01_request_condor_write_scitoken(self):
        core.skip_ok_unless_installed('htcondor-ce', 'condor')
        self.skip_ok_if(core.PackageVersion('condor') <= '8.9.4',
                        'HTCondor version does not support SciToken submission')
        hostname = core.get_hostname()
        credentials.request_scitoken(
            "condor_write",
            scope="condor:/READ condor:/WRITE",
            audience=f"{hostname}:9619",
            overwrite=True
        )

    def test_02_request_xrootd_scitokens(self):
        self.skip_ok_unless("SCITOKENS" in core.config.get('xrootd.security', set()),
                            "Not using SciTokens for XRootD")
        try:
            credentials.request_scitoken(
                "xrootd",
                subject=core.options.username,
                scope=f"read:/ write:/{core.config['xrootd.user_subdir']}",
                audience="OSG_TEST",
                overwrite=True,
                log=True,
            )
            credentials.request_scitoken(
                "xrootd_tpc_1",
                subject=core.options.username,
                scope="read:/",
                audience="OSG_TEST",
                overwrite=True,
                log=True,
            )
            credentials.request_scitoken(
                "xrootd_tpc_2",
                subject=core.options.username,
                scope=f"write:/{core.config['xrootd.user_subdir']}",
                audience="OSG_TEST",
                overwrite=True,
                log=True,
            )
        except error.URLError as exc:
            self.fail(f"Failed to request token from demo.scitokens.org:\n{exc}")

import json
import os
import pwd
import time

from urllib import error, request

import osgtest.library.core as core
import osgtest.library.files as files
import osgtest.library.osgunittest as osgunittest

# Headers so that heroku doesn't block us
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko)' +
                         'Chrome/35.0.1916.47 Safari/537.36',
           'Content-Type': 'application/json'}


def request_demo_scitoken(scope, audience='ANY'):
    """Request a token with 'scope' from the demo SciTokens issuer
    """

    payload_dict = {'aud': audience,
                    'ver': 'scitokens:2.0',
                    'scope': scope,
                    'exp': int(time.time() + 3600),
                    'sub': 'osg-test'}
    payload = json.dumps({'payload': json.dumps(payload_dict),
                          'algorithm': 'ES256'}).encode()

    req = request.Request('https://demo.scitokens.org/issue',
                          data=payload,
                          headers=HEADERS)

    return request.urlopen(req).read()


class TestTokens(osgunittest.OSGTestCase):

    def test_01_request_condor_write_scitoken(self):
        core.state['token.condor_write_created'] = False
        core.config['token.condor_write'] = '/tmp/condor_write.scitoken'

        core.skip_ok_unless_installed('htcondor-ce', 'condor')
        self.skip_ok_if(core.PackageVersion('condor') <= '8.9.4',
                        'HTCondor version does not support SciToken submission')
        self.skip_ok_if(os.path.exists(core.config['token.condor_write']),
                        'SciToken with HTCondor WRITE already exists')

        hostname = core.get_hostname()
        try:
            token = request_demo_scitoken('condor:/READ condor:/WRITE', audience=f'{hostname}:9619')
        except error.URLError as exc:
            self.fail(f"Failed to request token from demo.scitokens.org:\n{exc}")

        ids = (0, 0)
        if core.state['user.verified']:
            user = pwd.getpwnam(core.options.username)
            ids = (user.pw_uid, user.pw_gid)

        files.write(core.config['token.condor_write'], core.to_str(token), backup=False, chown=ids)
        core.state['token.condor_write_created'] = True

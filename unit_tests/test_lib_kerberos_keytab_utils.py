import mock
from unittest.mock import (
    patch,
    mock_open
)

import lib.kerberos.kerberos_keytab_utils as kerberos_keytab_utils
import unit_tests.test_utils

import tarfile
import shutil
import subprocess  # noqa


class TestKerberosKeytabUtils(unit_tests.test_utils.CharmTestCase):

    def setUp(self):
        super(TestKerberosKeytabUtils, self).setUp()
        self.obj = kerberos_keytab_utils
        self.patches = ['config', 'resource_get', 'status_set']
        self.patch_all()

    @patch.object(tarfile, 'open')
    def test_check_resource_valid_archive(self, tarfile_open):
        self.resource_get.return_value = 'targzfile'
        tarfile_open.return_value = 'handle'

        self.assertTrue(kerberos_keytab_utils.check_resource())

    @patch.object(tarfile, 'open')
    def test_check_resource_invalid_archive(self, tarfile_open):
        self.resource_get.return_value = 'targzfile'
        tarfile_open.side_effect = tarfile.ReadError()

        self.assertFalse(kerberos_keytab_utils.check_resource())

    @patch.object(kerberos_keytab_utils, 'check_resource')
    @patch.object(kerberos_keytab_utils, 'calculate_and_store_keytab_checksum')
    @patch.object(kerberos_keytab_utils, 'gethostname')
    @patch.object(shutil, 'move')
    @patch.object(tarfile, 'open')
    def test_update_keytab_valid_resource(
            self,
            tarfile_open,
            shutil_move,
            gethostname,
            calculate_and_store_keytab_checksum,
            check_resource,
    ):
        check_resource.return_value = True

        def config_side_effect(key):
            return {
                'user': 'testuser',
                'principal': 'testprincipal',
            }[key]

        self.config.side_effect = config_side_effect

        gethostname.return_value = 'testhost'

        with patch('subprocess.check_call') as _subp_check_call:
            kinit_cmd = ['sudo', '-u', self.config('user'), 'kinit', '-t',
                         kerberos_keytab_utils.KEYTAB_PATH,
                         '{}/{}'.format(self.config('principal'),
                                        gethostname())]
            self.assertTrue(kerberos_keytab_utils.update_keytab())
            _subp_check_call.assert_called_with(kinit_cmd)

    @patch.object(kerberos_keytab_utils, 'check_resource')
    def test_update_keytab_invalid_resource(
            self,
            check_resource,
    ):
        check_resource.return_value = False

        self.assertFalse(kerberos_keytab_utils.update_keytab())

        with patch('subprocess.check_call') as _subp_check_call:
            _subp_check_call.assert_not_called()

    @patch.object(kerberos_keytab_utils, 'Template')
    @patch.object(kerberos_keytab_utils, 'check_resource')
    def test_render_config(
            self,
            check_resource,
            template,
    ):
        config = {
            'realm': 'Testrealm',
            'domain': 'testdomain',
            'kdc-address': 'testkdchost',
            'admin-server-address': 'testadminserverhost',
        }
        expected_context = {
            'default_realm': 'Testrealm',
            'default_realm_lower': 'testrealm',
            'default_domain': 'testdomain',
            'kdc_address': 'testkdchost',
            'admin_server_address': 'testadminserverhost',
        }

        def config_side_effect(key=None):
            if key is None:
                return config
            return config[key]

        self.config.side_effect = config_side_effect

        template_obj = template()

        with patch('builtins.open', mock_open()) as _mock_open:
            kerberos_keytab_utils.render_config()
            template_obj.render.assert_called_with(expected_context)

            f = _mock_open()

            _mock_open.assert_has_calls([
                mock.call('templates/krb5.conf', 'r'),
                mock.call('/etc/krb5.conf', 'w'),
            ], any_order=True)

            f.write.assert_has_calls([
                mock.call(template_obj.render())], any_order=True)

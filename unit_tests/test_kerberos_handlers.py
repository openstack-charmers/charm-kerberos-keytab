import mock
import charms.reactive
import unit_tests.test_utils

from unittest.mock import patch
import charms_openstack.test_utils as test_utils

# Mock out reactive decorators prior to importing reactive.kerberos_keytab
dec_mock = mock.MagicMock()
dec_mock.return_value = lambda x: x
charms.reactive.hook = dec_mock
charms.reactive.when = dec_mock
charms.reactive.when_not = dec_mock

import reactive.kerberos_keytab as handlers


class TestRegisteredHooks(test_utils.TestRegisteredHooks):

    def test_hooks(self):
        # test that the hooks actually registered the relation expressions that
        # are meaningful for this interface: this is to handle regressions.
        # The keys are the function names that the hook attaches to.
        hook_set = {
            'when': {
                'config_changed': ('config.changed', 'kerberos.installed'),
                'keytab_update_requested': (
                    'kerberos.keytab-update-requested', ),
            },
            'when_not': {
                'install': ('kerberos.installed', ),
            },
        }
        # test that the hooks were registered via the
        # reactive.kerberos_keytab
        self.registered_hooks_test_helper(handlers, hook_set, [])


class TestHandlers(unit_tests.test_utils.CharmTestCase):

    def setUp(self):
        super(TestHandlers, self).setUp()
        self.obj = handlers
        self.patches = [
            'status_set',
            'set_flag',
            'clear_flag',
        ]
        self.patch_all()

    @patch.object(handlers, 'update_keytab')
    @patch.object(handlers, 'render_config')
    def test_install_with_resource(self, render_config, update_keytab):
        update_keytab.return_value = True
        handlers.install()
        self.set_flag.assert_called_with('kerberos.installed')

    @patch.object(handlers, 'update_keytab')
    @patch.object(handlers, 'render_config')
    def test_install_without_resource(self, render_config, update_keytab):
        update_keytab.return_value = False
        handlers.install()
        self.set_flag.assert_not_called()

    @patch.object(handlers, 'render_config')
    def test_config_changed(self, render_config):
        handlers.config_changed()
        render_config.assert_called()

    @patch.object(handlers, 'update_keytab')
    @patch.object(handlers, 'check_keytab_for_upgrade_needed')
    def test_keytab_update_requested_needed_success(
            self,
            check_keytab_for_upgrade_needed,
            update_keytab):
        update_keytab.return_value = True
        check_keytab_for_upgrade_needed.return_value = True
        handlers.keytab_update_requested()
        self.clear_flag.assert_called_with('kerberos.keytab-update-requested')

    @patch.object(handlers, 'update_keytab')
    @patch.object(handlers, 'check_keytab_for_upgrade_needed')
    def test_keytab_update_requested_needed_failure(
            self,
            check_keytab_for_upgrade_needed,
            update_keytab):
        update_keytab.return_value = False
        check_keytab_for_upgrade_needed.return_value = True
        handlers.keytab_update_requested()
        self.clear_flag.assert_not_called()

    @patch.object(handlers, 'update_keytab')
    @patch.object(handlers, 'check_keytab_for_upgrade_needed')
    def test_keytab_update_requested_not_needed_success(
            self,
            check_keytab_for_upgrade_needed,
            update_keytab):
        update_keytab.return_value = True
        check_keytab_for_upgrade_needed.return_value = False
        handlers.keytab_update_requested()
        self.clear_flag.assert_not_called()

    @patch.object(handlers, 'update_keytab')
    @patch.object(handlers, 'check_keytab_for_upgrade_needed')
    def test_keytab_update_requested_not_needed_failure(
            self,
            check_keytab_for_upgrade_needed,
            update_keytab):
        update_keytab.return_value = False
        check_keytab_for_upgrade_needed.return_value = False
        handlers.keytab_update_requested()
        self.clear_flag.assert_not_called()

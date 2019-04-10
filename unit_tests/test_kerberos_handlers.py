# import mock

import reactive.kerberos_keytab as handlers
import charms_openstack.test_utils as test_utils


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

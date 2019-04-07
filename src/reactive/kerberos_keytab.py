import os
from socket import gethostname
import subprocess

from kerberos.kerberos_keytab_utils import (
    check_keytab_for_upgrade_needed,
    render_config,
    update_keytab,
)

from charms.reactive import (
    hook,
    remove_state,
    set_state,
    when,
    when_not,
)
from charmhelpers.core import (
    hookenv,
    unitdata,
)

@when_not('kerberos.installed')
def install():
    render_config()
    if update_keytab():
        set_state('kerberos.installed')


@when('config.changed')
@when('kerberos.installed')
def config_changed():
    render_config()


@when('kerberos.keytab-update-requested')
def keytab_update_requested():
    hookenv.status_set('maintenance', 'Starting keytab update')
    if check_keytab_for_upgrade_needed():
        if update_keytab():
            remove_state('kerberos.keytab-update-requested')

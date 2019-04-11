
from kerberos.kerberos_keytab_utils import (
    check_keytab_for_upgrade_needed,
    render_config,
    update_keytab,
)

from charms.reactive import (
    clear_flag,
    set_flag,
    when,
    when_not,
)

from charmhelpers.core.hookenv import (
    status_set
)


@when_not('kerberos.installed')
def install():
    render_config()
    if update_keytab():
        set_flag('kerberos.installed')


@when('config.changed')
@when('kerberos.installed')
def config_changed():
    render_config()


@when('kerberos.keytab-update-requested')
def keytab_update_requested():
    status_set('maintenance', 'Starting keytab update')
    if check_keytab_for_upgrade_needed():
        if update_keytab():
            clear_flag('kerberos.keytab-update-requested')

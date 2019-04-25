import hashlib
import subprocess
import tarfile
import shutil
from socket import gethostname, getfqdn
from jinja2 import Template


from charmhelpers.core import unitdata
from charmhelpers.core.hookenv import (
    config,
    resource_get,
    status_set,
)


KEYTAB_PATH = '/etc/krb5.keytab'
CHECKSUM_PREFIX = 'keytab.'
RESOURCE = 'keytab_bundle'

db = unitdata.kv()


def check_resource():
    ''' Check if the keytab bundle exists and attempt to open it '''
    bundle = resource_get(RESOURCE)
    if not bundle:
        status_set(
            'blocked',
            'No keytab bundle specified, please upload a bundle to proceed')
        return False
    try:
        tarfile.open(bundle)
    except tarfile.ReadError:
        status_set(
            'blocked',
            'Keytab bundle cannot be extracted.'
            ' Re-upload and run update-keytab')
        return False
    status_set('maintenance', 'Keytab bundle found, continuing')
    return True


def update_keytab():
    ''' Update the keytab file on disk and use kinit to generate a new
        certificate cache.
    '''
    status_set('maintenance', 'Updating keytab file')
    if check_resource():
        hostname = gethostname().lower()
        bundle = resource_get(RESOURCE)
        keytab_bundle = tarfile.open(bundle)
        keytab_bundle.extract('%s.keytab' % hostname, path='/etc')
        shutil.move('/etc/%s.keytab' % hostname, KEYTAB_PATH)
        subprocess.check_call(
            ['sudo', '-u', config('user'), 'kinit', '-t', KEYTAB_PATH,
             parse_principal_template(config('principal'))])
        calculate_and_store_keytab_checksum()
        status_set('active', 'Unit is ready.')
        return True
    return False


def parse_principal_template(template):
    ''' Replace strings in template with the upper/lower/fqdn/short hostname
        by parsing the hostname and replacing strings with the various values
    '''
    fqdn_lower = getfqdn().lower()
    FQDN_UPPER = fqdn_lower.upper()
    shorthostname_lower = gethostname().split('.')[0].lower()
    SHORTHOSTNAME_UPPER = shorthostname_lower.upper()

    principal = template

    principal = principal.replace('{hostname}', gethostname())
    principal = principal.replace('{fqdn}', fqdn_lower)
    principal = principal.replace('{FQDN}', FQDN_UPPER)
    principal = principal.replace('{short}', shorthostname_lower)
    principal = principal.replace('{SHORT}', SHORTHOSTNAME_UPPER)

    return principal


def render_config():
    ''' Given the provided charm config render the krb5 configuration '''
    ctxt = {}
    charm_config = config()
    ctxt['default_realm'] = charm_config['realm']
    ctxt['default_realm_lower'] = charm_config['realm'].lower()
    ctxt['default_domain'] = charm_config['domain']
    ctxt['kdc_address'] = charm_config['kdc-address']
    ctxt['admin_server_address'] = (charm_config['admin-server-address'] or
                                    charm_config['kdc-address'])
    with open('templates/krb5.conf', 'r') as t:
        krb5_template = Template(t.read())
    with open('/etc/krb5.conf', 'w') as f:
        f.write(krb5_template.render(ctxt))
    status_set('active', 'Unit is ready.')


def check_keytab_for_upgrade_needed():
    ''' Return True if the keytab bundle has changed '''
    status_set('maintenance', 'Checking keytab resources')
    key = CHECKSUM_PREFIX + RESOURCE
    old_checksum = db.get(key)
    new_checksum = calculate_keytab_checksum(RESOURCE)
    if new_checksum != old_checksum:
        return True
    return False


def calculate_keytab_checksum(resource):
    ''' Calculate a checksum for a resource '''
    md5 = hashlib.md5()
    path = resource_get(RESOURCE)
    if path:
        with open(path, 'rb') as f:
            data = f.read()
        md5.update(data)
    return md5.hexdigest()


def calculate_and_store_keytab_checksum():
    key = CHECKSUM_PREFIX + RESOURCE
    checksum = calculate_keytab_checksum(RESOURCE)
    db.set(key, checksum)

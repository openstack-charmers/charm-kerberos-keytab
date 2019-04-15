# Overview

Provides basic functionality to join an ubuntu server to a Kerberos domain using
a pregenerated keytab file.

# Usage

From an existing KDC or Kerberos-enabled AD server create one or more principals
for the units you wish to add to your domain.

  - For each host create $HOSTNAME.keytab
  - Tar the resulting files into keytab.tar

It is important to have this file created before deploying the charm. This file
can then be used during application deployment:

  - juju deploy kerberos-keytab --resource keytab_bundle=<path-to-file>.tar
  - juju add-relation kerberos-keytab <some-other-principal-charm>

# Configuration

This charm assumes the Kerberos domain and realm to be EXAMPLE.COM, which is
likely incorrect for your environment. This should be changed before relating
it to any other units.

# Contact Information

Michael Skalka
michael.skalka@canonical.com

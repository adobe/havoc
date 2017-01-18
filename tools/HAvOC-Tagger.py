#!/usr/bin/env python
"""
HAvOC (HAproxy clOud Configuration)
Generate HAproxy Configuration based on AWS/OpenStack API
"""

__version = 0.2

import logging, os, sys, re
import socket

from subprocess import call
from optparse import OptionParser

try:
    import boto.ec2
    AWS = True
except:
    AWS = False

try:
    from novaclient import client
    NOVA = True
except:
    NOVA = False

# Define command line options
getopt = OptionParser(version="%%prog %s" % __version,
    usage="Usage: %prog [options]")
getopt.add_option("-i", "--access_key_id", dest="access_key_id", type="string", metavar="ACCESS_KEY_ID",
    help="AWS ACCESS KEY ID")
getopt.add_option("-s", "--access_key_secret", dest="access_key_secret", type="string", metavar="ACCESS_KEY_SECRET",
    help="AWS ACCESS KEY SECRET")
getopt.add_option("-r", "--overflow-aws-region", dest="overflow_aws_region", type="string", metavar="REGION",
    help="OVERFLOW AWS REGION")
getopt.add_option("-z", "--overflow-aws-zone", dest="overflow_aws_zone", type="string", metavar="ZONE",
    help="OVERFLOW AWS ZONE")

if NOVA:
    getopt.add_option("-a", "--os-auth-url", dest="os_auth_url", type="string", metavar="AUTH_URL",
        help="OS AUTH URL")
    getopt.add_option("-u", "--os-username", dest="os_username", type="string", metavar="USERNAME",
        help="OS USERNAME")
    getopt.add_option("-k", "--os-api-key", dest="os_api_key", type="string", metavar="API_KEY",
        help="OS API KEY")
    getopt.add_option("-P", "--os-project-id", dest="os_project_id", type="string", metavar="PROJECT_ID",
        help="OS PROJECT ID")

getopt.add_option("-p", "--prefix", dest="prefix", type="string", metavar="HOSTNAME_PREFIX",
        help="Hostname Prefix")
getopt.add_option("-t", "--tag", dest="tag_key", type="string", metavar="TAG_KEY",
        help="Tag Key")
getopt.add_option("-v", "--value", dest="tag_value", type="string", metavar="TAG_VALUE",
        help="Tag Value")

(options, args) = getopt.parse_args();

if not all([options.prefix, options.tag_key, options.tag_value]):
    print getopt.format_help()
    sys.exit(65)

if not all([options.access_key_id, options.access_key_secret, options.overflow_aws_region]):
    AWS = False
if not all([options.os_auth_url, options.os_username, options.os_api_key, options.os_project_id]):
    NOVA = False

# Create services
if AWS:
    ec2 = boto.ec2.connect_to_region(options.overflow_aws_region, aws_access_key_id=options.access_key_id, aws_secret_access_key=options.access_key_secret)
if NOVA:
    nova = client.Client("2", auth_url=options.os_auth_url, username=options.os_username, api_key=options.os_api_key, project_id=options.os_project_id)

# AWS
if AWS:
    filtering={'tag:hostname': options.prefix + '*'}
    if options.overflow_aws_zone is not None:
        filtering['availability_zone'] = options.overflow_aws_zone
    res = ec2.get_all_instances(filters=filtering)
    for r in res:
        for i in r.instances:
            print "Doing", i.tags['hostname'], "tag:", options.tag_key, "=>", options.tag_value
            ec2.create_tags([i.id], {options.tag_key: options.tag_value})

# OS
# XXX: filtering on metadata in OpenStack is currently not working. Needs further investigation.
if NOVA:
    res = nova.servers.list(search_opts={'metadata': u'{"hostname":"%s"}'%options.prefix + '*', 'all_tenants': 0})
    for i in res:
        if 'hostname' in i.metadata and options.prefix in i.metadata['hostname']:
            print "Doing", i.name, "tag:", options.tag_key, "=>", options.tag_value
            nova.servers.set_meta(i.id, {options.tag_key: options.tag_value})

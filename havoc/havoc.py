#!/usr/bin/env python
# encoding: utf-8

"""
HAvOC (HAproxy clOud Configuration)
Generate HAproxy Configuration based on AWS and Openstack API (Nova). Leverage Jinja2 for templating.
"""

import logging, os, sys, re

from subprocess import call
import hashlib
import jinja2
from jinja2 import Environment, PackageLoader

import boto.ec2
from novaclient import client


class Havoc(object):

    def __init__(self, ec2, nova, options, log):
        self.ec2 = ec2
        self.nova = nova
        self.log = log
        self.options = options


    def get_ec2_instances_in_pool(self, pool):
        instances = []
        if self.ec2 is None:
            self.log.debug('EC2 provider is not setup. No instances will be returned for this pool : %s', pool)
            return instances

        filters = {'tag:pool': pool,'instance-state-name': 'running'}
        if self.options['vpc'] is not None:
            filters['tag:vpc'] = self.options['vpc']

        if self.options['overflow_aws_zone'] is not None:
            filters['availability_zone'] = self.options['overflow_aws_zone']

        try:
            res = self.ec2.get_all_instances(filters=filters)
        except Exception as e:
            self.log.error("Error listing instances for EC2 : %s", e)
            return instances

        for r in res:
            for i in r.instances:
                if 'hostname' in i.tags:
                    i.name = i.tags['hostname'] + "_aws"
                else:
                    i.name = i.public_dns_name
                instances.append(i)
        return instances

    def get_os_instances_in_pool(self, pool):
        self.log.debug("Openstack : Trying to find vm in %s", pool)
        instances = []
        if self.nova is None:
            self.log.debug('Nova provider is not setup. No instances will be returned for this pool : %s', pool)
            return instances

        res = self.nova.servers.list(search_opts={'metadata': u'{"pool":"%s"}'%pool, 'all_tenants': 0})
        for i in res:
            try:
                for net, confs in i.addresses.items():
                    for conf in confs:
                        if conf['OS-EXT-IPS:type'] == 'fixed':
                            i.ip_address = conf['addr']
                            i.name = i.name + "_cm"
                            if 'pool' in i.metadata and i.metadata['pool'] == pool:
                                self.log.debug("Found instances %s for pool %s", i.name, pool)
                                instances.append(i)
            except Exception as e:
                self.log.debug('Cannot get information for the instances: %s', e)
                pass
        return instances

    def build_haproxy_conf(self, template, instances, hostname, cpu_count, cpu_reserved):
        try:
            with open(template, 'r') as handle:
                template_source = handle.read()
        except Exception as e:
            self.log.debug("Error opening template : %s", e)
            return False
        handle.close()

        jinja_env = Environment()
        template = jinja_env.from_string(template_source)

        template_data = template.render(instances=instances, hostname=hostname, cpu_count=cpu_count, cpu_reserved=cpu_reserved)

        if self.options['dry_run']:
            self.log.info("Dry run. HAproxy configuration :\n%s", template_data)
            return True

        if self.do_we_have_changes(template_data):
            self.log.debug('Writing HAproxy configuration to file : %s and reloading HAproxy service', self.options['haproxy_cfg'])
            try:
                with open(self.options['haproxy_cfg'], 'w') as config:
                    config.write(template_data)
                    config.close()
            except Exception as e:
                self.log.debug("Error while manipulating haproxy.cfg :\n%s", e)
                return False

            return self.reload_haproxy()

    def do_we_have_changes(self, template_data):
        file_md5 = hashlib.md5()
        try:
            with open(self.options['haproxy_cfg'], 'r') as config:
                file_md5.update(config.read().encode())
                config.close()
        except Exception as e:
            self.log.error("Error accessing HAproxy configuration : %s", e)
            return False

        data_md5 = hashlib.md5()
        data_md5.update(template_data.encode())

        return data_md5.hexdigest() == file_md5.hexdigest()

    def reload_haproxy(self):
        try:
            sysinit = os.readlink('/proc/1/exe')
        except Exception as e:
            self.log.error("Cannot determine system init. Will not reload HAproxy service")
            return False
        service = []

        if sysinit == 'systemd':
            service = ["systemctl", "reload", "haproxy"]
        else:
            service = ["service", "haproxy", "reload"]

        try:
            call(service)
        except Exception as e:
            self.log.error("Failed to reload HAproxy service : %s", e)
            return False

    def run(self):
        instances = {}

        # Retrieve instances
        for pool in self.options['pools'].split(','):
            ec2_instances = self.get_ec2_instances_in_pool(pool)
            os_instances = self.get_os_instances_in_pool(pool)
            instances[pool] = ec2_instances + os_instances

        # Building HAproxy configuratio based on Jinja2 template
        if self.build_haproxy_conf(self.options['template'], instances, "blabla.com", 10, 2):
            self.log.info('HAproxy configuration has been generated.')
            return 0

        return 1

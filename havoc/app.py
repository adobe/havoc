#!/usr/bin/env python
# encoding: utf-8

"""
HAvOC (HAproxy clOud Configuration)
Generate HAproxy Configuration based on AWS and Openstack API (Nova).
Leverage Jinja2 for templating.
"""

import logging, sys, re
import click
import daemon
import daemon.pidfile
from time import sleep

import boto.ec2
from novaclient import client

from havoc.core import Havoc
from havoc.config import Config


def get_logger(output, debug):
    loglevel = logging.INFO
    if debug:
        loglevel = logging.DEBUG
    logger = logging.getLogger('havoc')
    logger.setLevel(loglevel)
    output.setLevel(loglevel)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    output.setFormatter(formatter)
    logger.addHandler(output)
    return logger

def time_str_to_sec(time):
    w = {
        'sec': 1,
        'min': 60,
        'hour': 3600
    }
    res = re.match(r"(\d+)(\w+)", time)
    if res is not None and len(res.groups()) == 2:
        return int(res.group(1))*int(w[res.group(2)])
    # Default on 5min
    return 300

def run_daemon(havoc, log, run_every='5min'):
    while True:
        havoc.run()
        nextrun = time_str_to_sec(run_every)
        log.debug("Wait for next run : %d sec", nextrun)
        sleep(nextrun)


@click.command()
@click.option('--config', default="/etc/havoc/config.yaml", help="HAvOC configuration file (YAML format)")
@click.option('--cli', is_flag=True, help="Run HAvOC as a command without daemon")
@click.option('--daemonize', is_flag=True, help="Start the HAvOC daemon")
@click.option('--interval', default='5min', help="Define the interval between every run")
@click.option('--pidfile', default='/var/run/havoc.pid', help="Define the pidfile when running as daemon")
@click.option('--template', default='/etc/haproxy/haproxy.cfg.tmpl', help="Jinja 2 template")
@click.option('--haproxy-cfg', default='/etc/haproxy/haproxy.cfg', help="The HAproxy configuration file")
@click.option('--pools', required=True, default='', help="List of HAproxy Backend Pools")
@click.option('--cpus', default=1, help="Reserved CPUS for HAproxy (nbproc)")
@click.option('--system-cpus', default=0, help="Reserved CPUS for the system")
@click.option('--log-send-hostname', default=None, help="Hostname for the syslog header")
@click.option('--aws-access-key-id', default=None, help="AWS Access Key ID")
@click.option('--aws-access-key-secret', default=None, help="AWS Access Key Secret")
@click.option('--overflow-aws-region', default=None, help="Overflow AWS region")
@click.option('--overflow-aws-zone', default=None, help="Overflow AWS zone")
@click.option('--aws-vpc', default=None, help="AWS VPC name")
@click.option('--os-auth-url', default=None, help="Openstack Auth URL")
@click.option('--os-username', default=None, help="Openstack Username")
@click.option('--os-api-key', default=None, help="Openstack API Key")
@click.option('--os-project-id', default=None, help="Openstack Project ID")
@click.option('--os-tenant', default=None, help="Openstack tenant name")
@click.option('--logfile', default='/var/log/havoc.log', help="Logging file when the application is in daemon mode")
@click.option('--dry-run', is_flag=True, help="If use, HAvOC will display the result and not change haproxy.cfg")
@click.option('--debug', is_flag=True, help="Debug mode")
def cli(**options):
    """HAvOC (HAproxy clOud Configuration)

    Generate HAproxy Configuration based on AWS and Openstack API (Nova).

    HAvOC leverages Jinja2 for templating : http://jinja.pocoo.org/docs/dev/templates
    """

    # Parse configuration
    config = Config(options, options['config'])

    # Setup logging
    if config.get('daemonize'):
        log_handler = logging.FileHandler(config.get('logfile'))
    else:
        log_handler = logging.StreamHandler(sys.stdout)
    log = get_logger(log_handler, config.get('debug'))

    log.debug("Configuration : %s", config.get_config())

    # Validate pools
    if config.get('pools') is '':
        log.error("Pools is not defined. Please use --pools or pools in the configuration file")
        sys.exit(1)

    # Defining regions
    ec2 = None
    aws_region = config.get('overflow_aws_region') if config.get('overflow_aws_region') else "us-east-1"
    nova = None

    # Setup providers
    if config.get('aws_access_key_id') is not None:
        log.debug("Creating EC2 Provider, AWS Key ID: %s", config.get('aws_access_key_id'))
        ec2 = boto.ec2.connect_to_region(
                aws_region, aws_access_key_id=config.get('aws_access_key_id'), aws_secret_access_key=config.get('aws_secret_access_key')
                )

    if config.get('os_username') is not None:
        log.debug("Creating Openstack Provider, User: %s", config.get('os_username'))
        nova = client.Client("2",
                auth_url=config.get('os_auth_url'), username=config.get('os_username'), api_key=config.get('os_password'), project_id=config.get('os_project_id')
                )

    havoc = Havoc(ec2, nova, options, log)

    if config.get('cli'):
        sys.exit(havoc.run())

    if config.get('daemonize'):
        try:
            daemon_context = daemon.DaemonContext(
                pidfile=daemon.pidfile.PIDLockFile(config.get('pidfile')),
                stderr=sys.stderr,
                stdout=sys.stderr,
                files_preserve=[log_handler.stream]
            )
            with daemon_context:
                run_daemon(havoc, log, run_every=config.get('interval'))
        except Exception as e:
            log.error("Daemonize failed. Exiting : %s", e)
            sys.exit(1)
    else:
        run_daemon(havoc, log, run_every=config.get('interval'))


if __name__ == '__main__':
    cli()

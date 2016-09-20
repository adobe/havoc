#!/usr/bin/env python
# encoding: utf-8

"""
HAvOC (HAproxy clOud Configuration)
Generate HAproxy Configuration based on AWS and Openstack API (Nova). Leverage Jinja2 for templating.
"""

import logging, os, sys, re
import click
import daemon
import daemon.pidfile
from time import sleep

from havoc.havoc import Havoc


# <3 12Factor
def get_config(options, param, env_param):
    if param in options and options[param] is not None:
        return options[param]
    if env_param in os.environ and os.environ[env_param] is not None:
        return os.environ[env_param]
    return None

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
    res = re.match("(\d+)(\w+)", time)
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
@click.option('--cli', is_flag=True, help="Run HAvOC as a command without daemon")
@click.option('--daemonize', is_flag=True, help="Start the HAvOC daemon")
@click.option('--interval', default='5min', help="Define the interval between every run")
@click.option('--dry-run', is_flag=True, help="If use, HAvOC will display the result and not change haproxy.cfg")
@click.option('--pidfile', default='/var/run/havoc.pid', help="Define the pidfile when running as daemon")
@click.option('--template', default='/etc/haproxy/haproxy.cfg.tmpl', help="Jinja 2 tempalte")
@click.option('--haproxy-cfg', default='/etc/haproxy/haproxy.cfg', help="The HAproxy configuration file")
@click.option('--access_key_id', default=None, help="AWS Access Key ID")
@click.option('--access_key_secret', default=None, help="AWS Access Key Secret")
@click.option('--os-auth-url', default=None, help="Openstach Auth URL")
@click.option('--os-username', default=None, help="Openstach Username")
@click.option('--os-api-key', default=None, help="Openstach API Key")
@click.option('--os-project-id', default=None, help="Openstach Project ID")
@click.option('--overflow-aws-region', default=None, help="Overflow AWS region")
@click.option('--overflow-aws-zone', default=None, help="Overflow AWS zone")
@click.option('--vpc', default=None, help="AWS VPC or Openstack tenant name")
@click.option('--pools', required=True, default=None, help="List of HAproxy Backend Pools")
@click.option('--cpus', default=1, help="Reserved CPUS for HAproxy (nbproc)")
@click.option('--logfile', default='/var/log/havoc.log', help="Logging file when the application is in daemon mode")
@click.option('--debug', is_flag=True, help="Debug mode")
def cli(**options):
    """HAvOC (HAproxy clOud Configuration)

    Generate HAproxy Configuration based on AWS and Openstack API (Nova). Leverage Jinja2 for templating.
    """

    # CLI Parameters first
    options['access_key_id'] = get_config(options, 'access_key_id', 'AWS_ACCESS_KEY_ID')
    options['access_key_secret'] = get_config(options, 'access_key_secret', 'AWS_SECRET_ACCESS_KEY')
    options['os_auth_url'] = get_config(options, 'os_auth_url', 'OS_AUTH_URL')
    options['os_username'] = get_config(options, 'os_username', 'OS_USERNAME')
    options['os_password'] = get_config(options, 'os_password', 'OS_PASSWORD')
    options['os_project_id'] = get_config(options, 'os_project_id', 'OS_TENANT_NAME')
    options['vpc'] = get_config(options, 'vpc', 'OS_TENANT_NAME')

    # Setup logging
    if options['daemonize']:
        log_handler = logging.FileHandler(options['logfile'])
    else:
        log_handler = logging.StreamHandler(sys.stdout)
    log = get_logger(log_handler, options['debug'])

    log.debug("Config: %s", options)

    # Defining regions
    ec2 = None
    aws_region = "us-east-1"
    nova = None
    os_region = "tm-iad-1"

    # Setup providers
    if options['access_key_id'] is not None:
        log.debug("Creating EC2 Provider, AWS Key ID: %s", options['aws_access_key_id'])
        ec2 = boto.ec2.connect_to_region(aws_region, aws_access_key_id=options['access_key_id'], aws_secret_access_key=options['access_key_secret'])

    if options['os_username'] is not None:
        log.debug("Creating Openstack Provider, User: %s", options['os_username'])
        nova = client.Client("2", auth_url=options['os_auth_url'], username=options['os_username'], api_key=options['os_password'], project_id=options['os_project_id'])

    havoc = Havoc(ec2, nova, options, log)

    if options['cli']:
        sys.exit(havoc.run())

    if options['daemonize']:
        try:
            daemon_context = daemon.DaemonContext(
                pidfile=daemon.pidfile.PIDLockFile(options['pidfile']),
                stderr=sys.stderr,
                stdout=sys.stderr,
                files_preserve=[log_handler.stream]
            )
            with daemon_context:
                run_daemon(havoc, log, run_every=options['interval'])
        except Exception as e:
            log.error("Daemonize failed. Exiting : %s", e)
            sys.exit(1)
    else:
        run_daemon(havoc, log, run_every=options['interval'])


if __name__ == '__main__':
    cli()

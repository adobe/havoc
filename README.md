# HAvOC (HAproxy clOud Configuration)

Generate HAproxy Configuration based on AWS and Openstack API (Nova). Leverage Jinja2 for templating.

```
$ havoc --help
Usage: havoc [OPTIONS]

  HAvOC (HAproxy clOud Configuration)

  Generate HAproxy Configuration based on AWS and Openstack API (Nova).

  HAvOC leverages Jinja2 for templating :
  http://jinja.pocoo.org/docs/dev/templates

Options:
  --config TEXT               HAvOC configuration file (YAML format)
  --cli                       Run HAvOC as a command without daemon
  --daemonize                 Start the HAvOC daemon
  --interval TEXT             Define the interval between every run
  --pidfile TEXT              Define the pidfile when running as daemon
  --template TEXT             Jinja 2 template
  --haproxy-cfg TEXT          The HAproxy configuration file
  --pools TEXT                List of HAproxy Backend Pools  [required]
  --cpus INTEGER              Reserved CPUS for HAproxy (nbproc)
  --system-cpus INTEGER       Reserved CPUS for the system
  --log-send-hostname TEXT    Hostname for the syslog header
  --access_key_id TEXT        AWS Access Key ID
  --access_key_secret TEXT    AWS Access Key Secret
  --overflow-aws-region TEXT  Overflow AWS region
  --overflow-aws-zone TEXT    Overflow AWS zone
  --aws-vpc TEXT              AWS VPC name
  --os-auth-url TEXT          Openstack Auth URL
  --os-username TEXT          Openstack Username
  --os-api-key TEXT           Openstack API Key
  --os-project-id TEXT        Openstack Project ID
  --os-tenant TEXT            Openstack tenant name
  --os-tenant TEXT            Openstack tenant name
  --logfile TEXT              Logging file when the application is in daemon
                              mode
  --dry-run                   If use, HAvOC will display the result and not
                              change haproxy.cfg
  --debug                     Debug mode
  --help                      Show this message and exit.
```

## Installation

TODO

## Contributors

* Joseph Herlant ([aerostitch](https://github.com/aerostitch))
* Julien Fabre  ([pryz](https://github.com/pryz))
* Nicolas Brousse ([orieg](https://github.com/orieg))
* Oleg Galitskiy ([Galitskiy](https://github.com/Galitskiy))

# OpenStack Notification Listener Script

A sample Python CLI tool to listen for notifications (events) from RabbitMQ
message queues and log the information. It uses OpenStack messaging library
[`oslo_messaging`](https://docs.openstack.org/oslo.messaging/latest/reference/index.html) for
handling notifications and [`oslo_config`](https://docs.openstack.org/oslo.config/latest/) for
configuration management.

## Usage
```console
$ ./listen_notifications.py --help
usage: listen_notifications [-h] [--config-dir DIR] [--config-file PATH] [--log_level LOG_LEVEL]
                            [--shell_completion SHELL_COMPLETION] [--notification-log_payload]
                            [--notification-nolog_payload]
                            [--notification-publisher_id_filter NOTIFICATION_PUBLISHER_ID_FILTER]
                            [--rabbit-hosts RABBIT_HOSTS] [--rabbit-nosingle_threaded]
                            [--rabbit-password RABBIT_PASSWORD] [--rabbit-single_threaded]
                            [--rabbit-user RABBIT_USER] [--rabbit-virtual_host RABBIT_VIRTUAL_HOST]

options:
  -h, --help            show this help message and exit
  --config-file PATH    Path to a config file to use. Defaults to None.
  --log_level LOG_LEVEL
                        Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). (defaule: INFO)

Notification Options:
  --notification-log_payload
                        Whether to log the notification payload (default: True)
  --notification-nolog_payload
                        The inverse of --log_payload
  --notification-publisher_id_filter NOTIFICATION_PUBLISHER_ID_FILTER
                        Regular expression for filtering notifications based on
                        publisher_id. (default: '^(?!ceilometer).*')

RabbitMQ Options:
  --rabbit-hosts RABBIT_HOSTS
                        List of RabbitMQ hosts separated by comma
  --rabbit-nosingle_threaded
                        The inverse of --single_threaded
  --rabbit-password RABBIT_PASSWORD
                        RabbitMQ password (default: guest)
  --rabbit-single_threaded
                        Run listeners in a single thread handling all RabbitMQ hosts
                        (default: False)
  --rabbit-user RABBIT_USER
                        RabbitMQ username (default: guest))
  --rabbit-virtual_host RABBIT_VIRTUAL_HOST
                        RabbitMQ virtual host (default: openstack)
```

## Configuration

You can pass options using cli parameter, environemnt variable or configuration file.

**Environment Variables**

You can override configuration options using environment variables:

- `RABBIT_USER` : RabbitMQ username.
- `RABBIT_PASSWORD` : RabbitMQ password.
- `RABBIT_HOSTS` : Comma-separated list of RabbitMQ hosts.
- `RABBIT_VHOST` : RabbitMQ virtual host.

**Configuration File**

You can also use configuration files to set options. By default, the script does not read
any configuration files, but you can specify one using the `--config-file` option.

Example configuration file (config.conf):

```ini
[DEFAULT]
log_level = INFO

[rabbit]
user = guest
password = guest
hosts = localhost:5672
virtual_host = openstack
single_threaded = False

[notification]
publisher_id_filter = ^compute.*
```

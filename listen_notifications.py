#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenStack Notification Listener Script

A sample Python CLI tool to listen for notifications (events) from RabbitMQ message
queues and log the information. It utilizes the OpenStack messaging library
`oslo_messaging` to handle notifications and `oslo_config` for configuration
management.

Usage:
    python3 listen_notifications.py [options]

options:
  -h, --help            show this help message and exit
  --config-file PATH    Path to a config file to use.
  --log_level LOG_LEVEL
                        Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                        (defaule: INFO)

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


RabbitMQ options can also be defined using environment variables:
    RABBIT_USER      -  RabbitMQ username.
    RABBIT_PASSWORD  -  RabbitMQ password.
    RABBIT_HOSTS     -  Comma-separated list of RabbitMQ hosts.
    RABBIT_VHOST     -  RabbitMQ virtual host.
"""

import concurrent.futures
import logging
import os
import pprint
import signal
import sys
import threading
import time
import urllib.parse

from oslo_config import cfg
import oslo_messaging

# Register configuration options
cfg.CONF.register_cli_opt(
    cfg.StrOpt(
        "log_level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). (defaule: INFO)",
    )
)

# Define "rabbitmq" configuration group and options
rabbit_group = cfg.OptGroup(name="rabbit", title="RabbitMQ Options")
rabbit_opts = [
    cfg.StrOpt("user", default="guest", help="RabbitMQ username (default: guest))"),
    cfg.StrOpt(
        "password",
        default="guest",
        help="RabbitMQ password (default: guest)",
        secret=True,
    ),
    cfg.ListOpt(
        "hosts",
        default=[],
        help="List of RabbitMQ hosts separated by comma",
    ),
    cfg.StrOpt(
        "virtual_host",
        default="openstack",
        help="RabbitMQ virtual host (default: openstack)",
    ),
    cfg.BoolOpt(
        "single_threaded",
        default=False,
        help="Run listeners in a single thread handling all RabbitMQ hosts (default: False)",
    ),
]
cfg.CONF.register_group(rabbit_group)
cfg.CONF.register_cli_opts(rabbit_opts, group=rabbit_group)

# Define "notification" configuration group and options
notification_group = cfg.OptGroup(name="notification", title="Notification Options")
notification_opts = [
    cfg.StrOpt(
        "publisher_id_filter",
        default=r"^(?!ceilometer).*",
        help="Regular expression for filtering notifications based on publisher_id. (default: '^(?!ceilometer).*')",
    ),
    cfg.BoolOpt(
        "log_payload",
        default=True,
        help="Whether to log the notification payload (default: True)",
    ),
]
cfg.CONF.register_group(notification_group)
cfg.CONF.register_cli_opts(notification_opts, group=notification_group)

# Register RabbitMQ driver options to cli
# from oslo_messaging._drivers import impl_rabbit
# cfg.CONF.register_cli_opts(impl_rabbit.rabbit_opts, group='oslo_messaging_rabbit')


def setup_logging(log_level="INFO"):
    """
    Set up the logging configuration.

    Args:
        log_level (str): The log level to set for the logger. Accepts one of
            "DEBUG", "INFO", "WARNING", "ERROR", or "CRITICAL". Defaults to "INFO".
    """

    dict_level = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    datefmt = "%Y-%m-%d %H:%M:%S"
    msg_fmt = "%(asctime)s %(threadName)s %(module)s - %(funcName)s [%(levelname)s] %(message)s"

    log_level = dict_level[log_level]
    formatter = logging.Formatter(
        fmt=msg_fmt,
        datefmt=datefmt,
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)


class NotificationEndpoint:
    """
    Handles incoming notifications from RabbitMQ.

    The NotificationEndpoint class serves as an endpoint for receiving and handling
    notifications published to RabbitMQ topics. It utilizes the oslo_messaging library
    to listen for notifications and processes them according to the specified filters
    and configurations.

    Attributes:
        filter_rule (oslo_messaging.NotificationFilter):
            A filter that determines which notifications are processed
            based on publisher_id.
    """

    filter_rule = oslo_messaging.NotificationFilter(
        publisher_id=cfg.CONF.notification.publisher_id_filter
    )

    def _notify(self, ctxt, publisher_id, event_type, payload, metadata):
        """
        Processes incoming notifications by logging some information.

        Args:
            ctxt (dict): The context of the notification (e.g., security credentials, request ID).
            publisher_id (str): The ID of the publisher that sent the notification.
            event_type (str): The type of the event that triggered the notification.
            payload (dict): The payload of the notification containing event-specific data.
            metadata (dict): Additional metadata associated with the notification.
        """
        log_msg = f"notification received: publisher_id={publisher_id} event_type={event_type}"

        if cfg.CONF.notification.log_payload:
            log_msg += f" payload={pprint.pformat(payload)}"

        logging.info(log_msg)

    def audit(self, ctxt, publisher_id, event_type, payload, metadata):
        """Handle audit level notifications."""
        self._notify(ctxt, publisher_id, event_type, payload, metadata)

    def debug(self, ctxt, publisher_id, event_type, payload, metadata):
        """Handle debug level notifications."""
        self._notify(ctxt, publisher_id, event_type, payload, metadata)

    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        """Handle info level notifications."""
        self._notify(ctxt, publisher_id, event_type, payload, metadata)

    def warn(self, ctxt, publisher_id, event_type, payload, metadata):
        """Handle warning level notifications."""
        self._notify(ctxt, publisher_id, event_type, payload, metadata)

    def error(self, ctxt, publisher_id, event_type, payload, metadata):
        """Handle error level notifications."""
        self._notify(ctxt, publisher_id, event_type, payload, metadata)

    def critical(self, ctxt, publisher_id, event_type, payload, metadata):
        """Handle critical level notifications."""
        self._notify(ctxt, publisher_id, event_type, payload, metadata)

    def sample(self, ctxt, publisher_id, event_type, payload, metadata):
        """Handle sample level notifications."""
        self._notify(ctxt, publisher_id, event_type, payload, metadata)


def override_from_env(group, option, env_var, list_value=False):
    """
    Override a configuration option with a value from an environment variable, if it is set.

    Args:
        group (str): The name of the configuration group containing the option.
        option (str): The name of the configuration option to override.
        env_var (str): The name of the environment variable to read the value from.
        list_value (bool, optional): If True, the configuration option is a list, and the environment
            variable's value will be split by commas. Defaults to False.

    """
    value = os.environ.get(env_var)
    # If environment variable is set, override the option value
    if value:
        # If option is a list, split the environment variable value into a list
        if list_value:
            value = value.split(",")
        cfg.CONF.set_override(option, value, group=group)


def start_listener(host, shutdown_event):
    """
    Start the notification listener for the given RabbitMQ hosts.

    Args:
        hosts (str or list): RabbitMQ host string or list of host strings.
        shutdown_event (threading.Event): Event to signal shutdown.
    """

    # Access configuration options
    username = cfg.CONF.rabbit.user
    password = cfg.CONF.rabbit.password
    hosts = cfg.CONF.rabbit.hosts
    vhost = cfg.CONF.rabbit.virtual_host

    # Encode username and password
    username = urllib.parse.quote(username, safe="")
    password = urllib.parse.quote(password, safe="")

    if isinstance(hosts, list):
        # Single-thread. Join list of hosts into a comma-separated string
        hosts_str = ",".join([f"{username}:{password}@{host}" for host in hosts])
    else:
        # Multi-thread. Processing a single RabbitMQ host
        hosts_str = f"{username}:{password}@{host}"

    url = f"rabbit://{hosts_str}/{vhost}"

    transport = oslo_messaging.get_notification_transport(cfg.CONF, url=url)
    targets = [
        oslo_messaging.Target(topic="notifications"),
        oslo_messaging.Target(topic="notifications_bis"),
        oslo_messaging.Target(topic="versioned_notifications"),
    ]
    endpoints = [NotificationEndpoint()]

    oslo_listener = None
    # Create and start the listener
    try:
        oslo_listener = oslo_messaging.get_notification_listener(
            transport,
            targets,
            endpoints,
            executor="threading",
        )

        logging.info("Messaging starting on host %s", host)
        oslo_listener.start()
        # Wait until the shutdown event is set
        while not shutdown_event.is_set():
            time.sleep(1)
        logging.info("Shutdown event received on host %s", host)
    except Exception as e:
        logging.exception("An error occurred on host %s: %s", host, e)
    finally:
        if oslo_listener:
            oslo_listener.stop()
            oslo_listener.wait()
            logging.info("Listener stopped on host %s", host)


def manage_listeners():
    """Manages notification listeners."""

    # Create a shutdown event
    shutdown_event = threading.Event()

    # Handle signals to set the shutdown_event
    def handle_signals(signum, frame):
        logging.info("Received signal %s, shutting down...", signum)
        shutdown_event.set()

    # Register the handle_signals function to be called when SIGINT or SIGTERM
    signal.signal(signal.SIGINT, handle_signals)
    signal.signal(signal.SIGTERM, handle_signals)

    # Define number of threads
    num_workers = 1 if cfg.CONF.rabbit.single_threaded else len(cfg.CONF.rabbit.hosts)

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        if cfg.CONF.rabbit.single_threaded:
            futures = {
                executor.submit(
                    start_listener, cfg.CONF.rabbit.hosts, shutdown_event
                ): cfg.CONF.rabbit.hosts
            }
        else:
            futures = {
                executor.submit(start_listener, host, shutdown_event): host
                for host in cfg.CONF.rabbit.hosts
            }

        for future in concurrent.futures.as_completed(futures):
            host = futures[future]
            try:
                future.result()
            except Exception as e:
                logging.exception("Host %s generated an exception: %s", host, e)


def main():
    """Entry point for the Notification Listener Script."""

    # Parse configuration files and command-line arguments
    cfg.CONF(sys.argv[1:], default_config_files=[])

    # Initialize logging
    try:
        setup_logging(cfg.CONF.log_level.upper())
    except KeyError:
        sys.exit(f"Error: Invalid log level '{cfg.CONF.log_level}'")

    # Override configuration options with environment variables
    override_from_env("rabbit", "user", "RABBIT_USER")
    override_from_env("rabbit", "password", "RABBIT_PASSWORD")
    override_from_env("rabbit", "hosts", "RABBIT_HOSTS", list_value=True)
    override_from_env("rabbit", "virtual_host", "RABBIT_VHOST")

    logging.info(
        "Rabbit configurations - user: %s, hosts: %s, vhost :%s",
        cfg.CONF.rabbit.user,
        cfg.CONF.rabbit.hosts,
        cfg.CONF.rabbit.virtual_host,
    )
    logging.info(
        "notification configurations: publisher_id=%s",
        cfg.CONF.notification.publisher_id_filter,
    )
    if not cfg.CONF.rabbit.hosts:
        sys.exit("Error: Missing RabbitMQ hosts.")

    manage_listeners()


if __name__ == "__main__":
    main()

# vim: ts=4

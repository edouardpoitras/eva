"""
Contains all of Eva's logging facilities.
"""
import logging
import gossip
from eva import conf

class Logger(object):
    """
    The Logger class is a very light wrapper around Python's standard logging
    framework. It's primary purpose is to wrap every logging message into a
    method that fires triggers on messages. This allows for plugins to act on
    certain log messages.

    It should not be necessary to instantiate this class manually as this is
    already done in the __init__.py file. Use `from eva import log` to use a
    singleton instance of this class.
    """
    def __init__(self):
        """
        Initializes the standard Python logging class at the appropriate level
        set in the Eva configuration file. Will also specify the appropriate
        logging format.
        """
        level = getattr(logging, conf['logging']['log_level'])
        self.logger = logging.getLogger(conf['logging']['log_name'])
        self.logger.setLevel(level)
        ch = logging.StreamHandler()
        ch.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    def debug(self, message):
        """
        Simple wrapper around the standard Python logger's debug method.
        Fires the `eva.logger.debug` trigger.
        """
        self.logger.debug(message)
        gossip.trigger('eva.logger.debug', message=message)

    def info(self, message):
        """
        Simple wrapper around the standard Python logger's info method.
        Fires the `eva.logger.info` trigger.
        """
        self.logger.info(message)
        gossip.trigger('eva.logger.info', message=message)

    def warning(self, message):
        """
        Simple wrapper around the standard Python logger's warning method.
        Fires the `eva.logger.warning` trigger.
        """
        self.logger.warning(message)
        gossip.trigger('eva.logger.warning', message=message)

    def error(self, message):
        """
        Simple wrapper around the standard Python logger's error method.
        Fires the `eva.logger.error` trigger.
        """
        self.logger.error(message)
        gossip.trigger('eva.logger.error', message=message)

    def fatal(self, message):
        """
        Simple wrapper around the standard Python logger's fatal method.
        Fires the `eva.logger.fatal` trigger.
        """
        self.logger.fatal(message)
        gossip.trigger('eva.logger.fatal', message=message)

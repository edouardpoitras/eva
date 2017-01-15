"""
Any function that did not neatly fit in any other Eva python file.
"""

import os
import sys
import inspect
from urllib.parse import quote_plus
import gossip
from pymongo import MongoClient
from anypubsub import create_pubsub_from_settings
from eva import log
from eva import conf

def restart(args=[]): #pylint: disable=W0102
    """
    Function used to restart Eva.

    .. warning::

        This will restart Eva immediately and kill all running scheduler jobs.

    :param args: A list of arguments to feed Eva on restart.
    :type args: list
    """
    args.insert(0, sys.argv[0])
    os.execl(sys.executable, sys.executable, *args)

def get_mongo_client():
    """
    A helper function to get a MongoDB client object with the credentials, host,
    and port specified in the Eva configuration file.

    :return: A MongoClient configured for a Eva MongoDB connection.
    :rtype: `pymongo.MongoClient
        <http://api.mongodb.com/python/current/api/pymongo/mongo_client.html>`_
    """
    username = quote_plus(conf['mongodb']['username'])
    password = quote_plus(conf['mongodb']['password'])
    host = conf['mongodb']['host']
    port = conf['mongodb']['port']
    uri = 'mongodb://'
    if len(username) > 0:
        uri = uri + username
        if len(password) > 0:
            uri = uri + ':' + password + '@'
        else:
            uri = uri + '@'
    uri = '%s%s:%s' %(uri, host, port)
    return MongoClient(uri)

def get_pubsub():
    """
    Helper function to get the pubsub client used to send and receive messages.

    :return: The pubsub object used to publish Eva messages to the clients.
    :rtype: `anypubsub.interfaces.PubSub  <https://github.com/smarzola/anypubsub>`_
    """
    mongo_client = get_mongo_client()
    return create_pubsub_from_settings({'backend': 'mongodb',
                                        'client': mongo_client,
                                        'database': 'eva',
                                        'collection': 'communications'})

def publish(message, channel='eva_messages'):
    """
    A helper function used to broadcast messages to all available Eva clients.

    :todo: Needs to be thoroughly tested (especially with audio data).
    :param message: The message to send to clients.
    :type message: string
    :param channel: The channel to publish in. The default channel that clients
        should be listening on is called 'eva_messages'.
    :type channel: string
    """
    log.info('Ready to publish message')
    gossip.trigger('eva.pre_publish', message=message)
    pubsub = get_pubsub()
    log.info('Publishing message: %s' %message)
    gossip.trigger('eva.publish', message=message)
    pubsub.publish(channel, message)
    gossip.trigger('eva.post_publish', message=message)

def get_calling_plugin(depth=2):
    """
    This method will inspect the ``depth`` level of the call stack to find
    which python module is responsible for the current method invocation.

    It is used when determining which plugin called the get/set output/input
    text/audio methods in the context object.

    :param depth: How deep to look down the call stack (2 for calling function).
    :type depth: integer
    """
    stack = inspect.stack()
    mod = inspect.getmodule(stack[depth][0])
    return mod.__name__

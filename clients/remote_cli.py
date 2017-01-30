#!/usr/bin/python3
"""
This client is similar to the Local CLI except that it does not bootstrap Eva
and so requires a running Eva server to connect to. The only dependency is the
anypubsub Python module.

The default settings assumes that the Eva MongoDB instance can be accessed locally::

	  pip3 install anypubsub --user
	  python3 clients/remote_cli.py

If this is not the case, the following code can be used to connect to the
remotely accessible MongoDB instance that Eva is using::

		from clients.remote_cli import RemoteCLI
		cli = RemoteCLI(host='remote.host', port=27017, username='', password='')
		cli.start_consumer('eva_messages')
		cli.start_consumer('eva_responses')
		cli.interact()
"""

from pymongo import MongoClient
from anypubsub import create_pubsub_from_settings
try:
    from cli import CLI
except ImportError:
    print('ERROR: Could not import base CLI class. Please make sure you ' + \
          'are running this from the Eva clients directory')
    # Ignoring error to allow sphinx to import class for documentation.
    CLI = object

class RemoteCLI(CLI):
    """
    Very similar to the LocalCLI class except that it requires a working Eva
    server and an accessible MongoDB instance holding the Eva database.
    """
    def __init__(self, host='localhost', port=27017, username='', password=''):
        super(RemoteCLI, self).__init__()
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.pubsub = self.get_pubsub()

    def get_pubsub(self):
        """
        Overriden method that returns the pubsub instance required to
        send/receive messages to/from Eva.

        :return: The pubsub object used to publish Eva messages to the clients.
        :rtype: `anypubsub.interfaces.PubSub  <https://github.com/smarzola/anypubsub>`_
        """
        uri = 'mongodb://'
        if len(self.username) > 0:
            uri = uri + self.username
            if len(self.password) > 0:
                uri = uri + ':' + self.password + '@'
            else:
                uri = uri + '@'
        uri = '%s%s:%s' %(uri, self.host, self.port)
        client = MongoClient(uri)
        return create_pubsub_from_settings({'backend': 'mongodb',
                                            'client': client,
                                            'database': 'eva',
                                            'collection': 'communications'})

    def get_results(self, command):
        """
        Overriden method that handles user input by sending the query/command
        to the Eva MongoDB instance. These messages are processed by Eva and
        a response is generated - which is then picked up by the client in
        a consumer thread.

        :param command: The query/command to send Eva.
        :type command: string
        """
        self.pubsub.publish('eva_commands', {'input_text': command})

def main():
    """
    Start a RemoteCLI instance.
    """
    cli = RemoteCLI()
    # Subscribe to messages and command responses.
    cli.start_consumer('eva_messages')
    cli.start_consumer('eva_responses', 'Eva Response: ')
    cli.interact()

if __name__ == '__main__':
    main()

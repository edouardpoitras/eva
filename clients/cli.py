"""
This file holds the abstract CLI class used to create command line utilities
that interact with Eva.

Please use the local_cli.py or remote_cli.py to interact with Eva via the
command line.
"""

import time
from multiprocessing import Process

class CLI(object):
    """
    Interface object used to create CLI-based Eva clients.
    Will take care of some of the heavy lifting, such as setting up the pubsub
    consumer for Eva messages and responses, and start the interaction loop.

    See the LocalCLI and RemoteCLI objects for examples.
    """
    def __init__(self):
        self.process = None

    def start_consumer(self, queue, response_prefix='Eva Message: '):
        """
        Start a pubsub consumer to receive messages from Eva.

        :param queue: The channel to receive messages from.
        :type queue: string
        :param response_prefix: A string that will prefix all messages from the queue.
        :type response_prefix: string
        """
        self.process = Process(target=self.consume_messages, args=(queue, response_prefix))
        self.process.start()

    def consume_messages(self, queue, response_prefix):
        """
        A method that consumes the messages from the queue specified.
        Will automatically print the messages to the CLI.
        This is the method used to fire off a separate process in the
        ``start_consumer`` method.
        It will continuously tail the MongoDB collection holding the messages.

        :param queue: The channel to receive messages from.
        :type queue: string
        :param response_prefix: A string that will prefix all messages from the queue.
        :type response_prefix: string
        """
        # Need to listen for messages and print them to the CLI.
        pubsub = self.get_pubsub()
        subscriber = pubsub.subscribe(queue)
        # Subscriber will continuously tail the mongodb collection queue.
        for message in subscriber:
            if message is not None:
                if isinstance(message, dict):
                    print('%s%s' %(response_prefix, message['output_text']))
                else:
                    print('%s%s' %(response_prefix, message))
            time.sleep(0.1)

    def get_pubsub(self):
        """
        A method meant to be overriden in order to get a pubsub object depending
        on the requirements of the CLI client.

        :return: An anypubsub object used to send and receive messages.
        :rtype: `anypubsub.interfaces.PubSub  <https://github.com/smarzola/anypubsub>`_
        """
        # Logic here to get the proper anypubsub object.
        pass

    def interact(self, command=None):
        """
        The main method that interacts with the Eva server.

        :param command: An optional command to send Eva. If None, this method
            will continuously poll the user for a new command/request after
            every response from Eva.
        :type command: string
        """
        if command is not None:
            results = self.get_results(command)
            self.handle_results(results)
        else:
            print('=== Eva CLI ===')
            while True:
                command = input('You: ')
                results = self.get_results(command)
                if results is not None:
                    self.handle_results(results)

    def get_results(self, command):
        """
        This method is meant to be overridden in order to properly process a
        command from the user and return Eva's response.

        :param command: The query/command to send Eva.
        :type command: string
        :return: Eva's response to that query/command.
        :rtype: string
        """
        pass

    def handle_results(self, results): #pylint: disable=R0201
        """
        This method performs the necessary actions with the data returned from
        Eva after a query/command.

        :param results: The response dict from Eva after a query/command.
            Will contain typically be a dict with the following structure::

                {
                    'output_text': <text_here>,
                    'output_audio': {
                        'audio': <audio_data>,
                        'content_type': <audio_content_type>
                    }
                }

        :type results: dict
        """
        if results['output_text'] is None:
            print('Eva Response: ')
        else:
            print('Eva Response: %s' %results['output_text'])

if __name__ == '__main__':
    print('Please use local_cli.py or remote_cli.py instead.')

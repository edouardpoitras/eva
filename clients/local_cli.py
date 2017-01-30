#!/usr/bin/python3
"""
Primary used for development and testing purposes.

The Local CLI is a text-only stand-alone client that does not require the Eva
server to be running in the background. Eva will be bootstrapped in the process
of running the Local CLI.

Ensure you have all the required dependencies installed and a local instance of
MongoDB running. You can also use the MongoDB instance available through the
docker-compose configuration provided::

		pip3 install -r requirements.txt --user
		docker-compose up mongo
		python3 clients/local_cli.py
"""

import sys
from eva import director
from eva.util import get_pubsub
try:
    from cli import CLI
except ImportError:
    print('ERROR: Could not import base CLI class. Please make sure you ' + \
          'are running this from the Eva clients directory')
    # Ignoring error to allow sphinx to import class for documentation.
    CLI = object

class LocalCLI(CLI):
    """
    A simple CLI Eva client.
    Does not require a running Eva server as it bootstraps Eva on every command.
    """
    def __init__(self):
        super(LocalCLI).__init__()
        director.boot()

    def get_pubsub(self):
        return get_pubsub()

    def get_results(self, cmd):
        return director.interact({'input_text': cmd})

def main():
    """
    Starts a local CLI client.
    """
    cli = LocalCLI()
    if len(sys.argv) > 1:
        command = ' '.join(sys.argv[1:])
        cli.interact(command)
    else:
        cli.start_consumer('eva_messages')
        cli.interact()

if __name__ == '__main__':
    main()

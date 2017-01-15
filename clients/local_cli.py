#!/usr/bin/python3
"""
A command line interface Eva client that directly calls Eva's director commands
in an attempt to send Eva commands without the need for an Eva server.

This is the easiest way to develop plugins in Eva.
"""

import sys
from cli import CLI
from eva import director
from eva.util import get_pubsub

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

#!/usr/bin/python3
"""
Convenience script to start up the Eva server.
"""

import eva.director
try:
    eva.director.serve()
except KeyboardInterrupt:
    print('You may need to CTRL-C a few more times...')

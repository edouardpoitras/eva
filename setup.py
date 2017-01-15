"""
Eva's setup.py file.
"""

from distutils.core import setup

setup(name='eva',
      version='0.1.0',
      description='Open source voice-enabled personal assistant.',
      author='Edouard Poitras',
      author_email='edouardpoitras@gmail.com',
      url='https://github.com/edouardpoitras/eva',
      install_requires=[
          "pymongo",
          "configobj",
          "gossip",
          "gitpython",
          "apscheduler",
          "anypubsub"
      ],
      packages=['eva']
     )

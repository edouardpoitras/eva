.. _clients:

Clients
=======

Eva uses a client-server model for it's distributed application structure.
Generally speaking, an effort is being made to keep the clients as simple as
possible in order to increase portability.
This is the reasoning behind the `Audio Server <https://github.com/edouardpoitras/eva-audio-server>`_
plugin - the clients only need to send audio data to Eva and let the plugins
take care of voice recognition.

Local CLI
---------

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

Remote CLI
----------

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

Headless (Experimental)
-----------------------

A simple voice-enabled client that has no user interface. It currently supports
keyword-based activation through either pocketsphinx or
`snowboy <https://snowboy.kitt.ai/>`_ models.

.. warning::

		This client is experimental and is currently under active development.

Requirements
++++++++++++

* Requires a working pyaudio installation (with portaudio)

    ``apt-get install portaudio19-dev``

    ``apt-get install python-pyaudio``

    Or

    ``pip3 install pyaudio --user``

* Requires pocketsphinx, webrtcvad, respeaker

    ``apt-get install pocketsphinx``

    ``pip3 install pocketsphinx webrtcvad``

    ``pip3 install git+https://github.com/respeaker/respeaker_python_library.git``

* May also need PyUSB

    ``pip3 install pyusb``

* Requires pydub for converting mp3 and ogg to wav for playback

    ``pip3 install pydub``

    See https://github.com/jiaaro/pydub for system dependencies.

    ``apt-get install ffmpeg libavcodec-ffmpeg-extra56``

    Or

    ``brew install ffmpeg --with-libvorbis --with-ffplay --with-theora``

* Requires anypubsub

    ``pip3 install anypubsub --user``

* Requires pymongo

    ``apt-get install python3-pymongo``

    Or

    ``pip3 install pymongo --user``

* Requires that Eva have the `Audio Server <https://github.com/edouardpoitras/eva-audio-server>`_ plugin enabled

Optional
++++++++

You may optionally use `snowboy`_ for keyword
detection. To do so, you need to get the ``_snowboydetect.so`` binary for your
platform (the one found at ``clients/snowboy/_snowboydetect.so`` in this repo is
only for Python3 on Ubuntu).

You can get precompiled binaries and information on how to compile
`here <https://github.com/kitt-ai/snowboy#precompiled-binaries-with-python-demo>`_.

If you end up compiling, ensure you use swig >= 3.0.10 and use your platform's
Python3 command in the Makefile (default is just ``python``).

Once you've compiled snowboy (or downloaded the dependencies), put the
``_snowboydetect.so`` and ``snowboydetect.py`` files in the ``clients/snowboy/``
folder.

You can either get a keyword detection model on the snowboy
`website <https://snowboy.kitt.ai/>`_ or use the provided alexa one in this
repository.

Usage
+++++

``python3 clients/headless.py``

Or with a snowboy model:

``python3 clients/headless.py --snowboy-model=clients/snowboy/alexa.umdl``

Desktop (Incomplete)
--------------------

A desktop client with a proper UI and taskbar icon is currently in the works.
The progress can be followed in the dev/desktop_client branch (help appreciated).

Developers
----------

The main way to communication with Eva is through the `communications` collection of Eva's main MongoDB instance.

There are three types of `channels` in the collection:

``eva_commands``

This channel is used to send commands or queries to Eva.
Eva will continuously listen on that channel for queries/commands from clients.

An entry looks something like this::

	{
  	"message" : {
    	"input_text" : "What is the current wind speed and humidity?",
    	"input_audio" : {
	    	"audio" : BinData(0, <data-here>),
	    	"content_type" : "audio/mpeg"
    	}
  	},
  	"type" : "message",
  	"channel" : "eva_commands",
  	"when" : ISODate("2017-01-25T03:00:00.000Z")
	}

The 'input_audio' key is not needed if 'input_text' is provided.

``eva_responses``

This is the channel the clients should be listening on.
All responses from Eva will be inserted into the MongoDB `communications` collection on this channel.

An entry looks something like this::

		{
			"message" : {
				"output_text" : "The current wind speed is 6.3 kilometers per hour. The current humidity is 94.0 percent",
				"output_audio" : {
					"audio" : BinData(0, <data-here>),
					"content_type" : "audio/mpeg"
				}
			},
			"type" : "message",
			"channel" : "eva_responses",
			"when" : ISODate("2017-01-25T03:00:01.000Z")
		}

``eva_messages``

This channel is used by Eva for notifications and to broadcast messages to all clients.

An entry looks something like this::

		{
			"channel" : "eva_messages",
			"when" : ISODate("2017-01-25T03:00:05.000Z"),
			"message" : "There is a severe thunderstorm warning in effect in your area",
			"type" : "message"
		}

In Python, the simplest way to send messages to Eva is to use the anypubsub Python module::

		from pymongo import MongoClient
		from anypubsub import create_pubsub_from_settings
		client = MongoClient(URI_OF_EVA_DB)
		pubsub = create_pubsub_from_settings({'backend': 'mongodb', 'client': client, 'database': 'eva', 'collection': 'communications'}
		pubsub.publish('eva_commands', {'input_text': 'command or query here'})

You can also use the anypubsub module to receive responses or notification/messages from Eva::

		from pymongo import MongoClient
		from anypubsub import create_pubsub_from_settings
		import time
		client = MongoClient(URI_OF_EVA_DB)
		pubsub = create_pubsub_from_settings({'backend': 'mongodb', 'client': client, 'database': 'eva', 'collection': 'communications'}

		subscriber = pubsub.subscribe('eva_responses')
		# Subscriber will continuously tail the mongodb collection channel.
		for message in subscriber:
				if message is not None:
						print(message['output_text'])
				time.sleep(0.1)

You would typically have a couple consumers (one for ``eva_responses`` and one
for ``eva_messages``) running in a separate thread. See clients/remote_cli.py
for a working example.

Don't forget to check out clients/headless.py for a working example with audio
and keyword activation.

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

.. automodule:: clients.local_cli

Remote CLI
----------

.. automodule:: clients.remote_cli

Headless (Experimental)
-----------------------

.. automodule:: clients.headless

Desktop (Incomplete)
--------------------

.. automodule:: clients.desktop

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

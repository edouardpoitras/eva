"""
This is where the magic begins. The director has functions to fire up Eva, load
all the plugins, and begin interactions with the clients.
"""

import time
import gossip
from eva.plugin import load_plugins
from eva.util import get_pubsub
from eva.context import EvaContext
from eva import log

def serve():
    """
    This is the one function you need to execute to start Eva.

    It begins the boot sequence, loads up all plugins, and starts listening for
    client interactions.
    """
    boot()
    pubsub = get_pubsub()
    # Notify connected clients that Eva has started successfully.
    pubsub.publish('eva_messages', 'Eva startup successful')
    # Start listening for commands.
    subscriber = pubsub.subscribe('eva_commands')
    # Subscriber will continuously tail the mongodb collection.
    for data in subscriber:
        if data is not None:
            handle_data_from_client(pubsub, data)
        time.sleep(0.1)

def handle_data_from_client(pubsub, data):
    """
    Helper function to fire off an interaction with Eva based on client data
    received, and then send off the response back to the clients.

    :param pubsub: The pubsub object used to publish Eva messages to the clients.
    :type pubsub: `anypubsub.interfaces.PubSub  <https://github.com/smarzola/anypubsub>`_
    :param data: The data received from Eva clients.
        See :func:`eva.context.EvaContext.__init__` for more details.
    :type data: dict
    """
    results = interact(data)
    pubsub.publish('eva_responses', results)

def boot():
    """
    The function that runs the Eva boot sequence and loads all the plugins.

    Fires the `eva.pre_boot` and `eva.post_boot` triggers.
    """
    log.info('Beginning Eva boot sequence')
    gossip.trigger('eva.pre_boot')
    load_plugins()
    gossip.trigger('eva.post_boot')
    log.info('Eva booted successfully')

def interact(data):
    """
    Eva's bread and butter function. Feeding data from the clients directly to
    this function will return a response dict, ready to be consumed by the
    clients as a response. This takes care of firing all the necessary triggers
    so that the plugins get a say in the responding text and/or audio.

    Fires the following triggers:
        * `eva.voice_recognition`
        * `eva.pre_interaction_context`
        * `eva.pre_interaction`
        * `eva.interaction`
        * `eva.post_interaction`
        * `eva.text_to_speech`
        * `eva.pre_return_data`

    :param data: The data received from the clients on query/command.
        See :func:`eva.context.EvaContext.__init__` for more details.
    :type data: dict
    :return: A dictionary with all the information necessary for the clients to
        handle the response appropriately. Typically something like this::

            dict {
                'output_text': The text of the response from Eva
                'output_audio': dict {
                    'audio': The binary audio data of the response (optional)
                    'content_type': The content type of the audio binary data (optional)
                }
            }

    :rtype: dict
    """
    log.info('Starting eva interaction')
    if 'input_text' in data:
        log.info('Interaction text provided: %s' %data['input_text'])
    if 'input_audio' in data:
        log.info('Interaction audio provided')
        if 'input_text' not in data:
            gossip.trigger('eva.voice_recognition', data=data)
    gossip.trigger('eva.pre_interaction_context', data=data)
    context = EvaContext(data)
    gossip.trigger('eva.pre_interaction', context=context)
    gossip.trigger('eva.interaction', context=context)
    gossip.trigger('eva.post_interaction', context=context)
    # Handle text-to-speech opportunity.
    if context.get_output_text() and not context.get_output_audio():
        gossip.trigger('eva.text_to_speech', context=context)
    # Prepare return data.
    return_data = get_return_data(context)
    # One last chance to modify the return data before sending to client.
    gossip.trigger('eva.pre_return_data', return_data=return_data)
    return return_data

def get_return_data(context):
    """
    This function is used to extract appropriate data from the context object
    before sending it to the Eva clients.

    It will check the context object for a text response and an audio response,
    and return a dict containing this information.

    :param context: The context object used for this interaction.
    :type context: :class:`eva.context.EvaContext`
    :return: A dict that may contain the key `output_text`, `output_audio`, or
        both. It should be identical to the return value of the :func:`interact`
        function barring any changes during the `eva.pre_return_data` trigger.
    :rtype: dict
    """
    return_data = {}
    if context.get_output_audio():
        log.info('Audio response generated')
        audio_data = {'audio': context.get_output_audio(),
                      'content_type': context.get_output_audio_content_type()}
        return_data['output_audio'] = audio_data
    else:
        log.info('This interaction yielded no output audio')
        return_data['output_audio'] = None
    if context.get_output_text():
        log.info('Response text: %s' %context.get_output_text())
        return_data['output_text'] = context.get_output_text()
    else:
        log.info('This interaction yielded no output text')
        return_data['output_text'] = None
    return return_data

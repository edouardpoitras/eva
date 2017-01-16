"""
Holds the EvaContext class - an integral part of every Eva interaction.
"""

import gossip
from eva.util import get_calling_plugin

class EvaContext(object):
    """
    An EvaContext object is passed along to plugins (via
    `gossip <https://gossip.readthedocs.io/en/latest/>`_ triggers) during
    an Eva interaction with the user. The object contains all the information
    required for the plugin to determine whether or not it should act on the
    current interaction.

    Plugin developers should always interact with Eva (and back out to the user)
    through the context object. This is important as the context object fires
    various triggers that enable other plugins to hook into ongoing interactions.
    """
    def __init__(self, data=None):
        """
        The data attribute is typically a dict with the following structure::

            dict {
                'input_text': The text/query provided by the client
                'input_audio': dict {
                    'audio': The binary audio data of the query (optional)
                    'content_type': The content type of the audio binary data (optional)
                }
                'output_text': The text of the response from Eva
                'output_audio': dict {
                    'audio': The binary audio data of the response(optional)
                    'content_type': The content type of the audio binary data (optional)
                }
            }

        It may also contain ``output_text`` and ``output_audio`` with the same
        format as it's ``input`` counterpart, but that is unlikely on initial
        creation of the context object (unless a plugin is doing something
        unorthodox on a trigger that's fired before interaction begins).

        Input in this case refers to text or audio that a client has sent Eva.
        Output refers to the resulting response from Eva that gets sent back.

        :param data: The data received from an Eva client.
        :type data: dict
        """
        #: The input text (query or command) from an Eva client.
        self.input_text = None
        #: The input audio binary data from an Eva client.
        self.input_audio = None
        #: The content type of the input audio binary data.
        self.input_audio_content_type = None
        #: The output text (response) from Eva.
        self.output_text = None
        #: The output audio binary data from Eva.
        self.output_audio = None
        #: The content type of the output audio binary data.
        self.output_audio_content_type = None
        #: True if a plugin has already handled the response, False otherwise.
        self.responded = False
        if data is not None:
            if 'input_text' in data:
                self.input_text = data['input_text']
            if 'input_audio' in data:
                if 'audio' in data['input_audio']:
                    self.input_audio = data['input_audio']['audio']
                if 'content_type' in data['input_audio']:
                    self.input_audio_content_type = data['input_audio']['content_type']
            if 'output_text' in data:
                self.output_text = data['output_text']
            if 'output_audio' in data:
                if 'audio' in data['output_audio']:
                    self.output_audio = data['output_audio']['audio']
                if 'content_type' in data['output_audio']:
                    self.output_audio_content_type = data['output_audio']['content_type']

    def get_input_text(self):
        """
        Method used by plugins to get the input text (query or command) from
        the Eva client for this interaction.

        :return: The input text from the Eva client this interaction.
        :rtype: string
        """
        if self.input_text is None:
            return ''
        return self.input_text

    def get_output_text(self):
        """
        Method used by plugins to get the output text (response) that has been
        generated so far by plugins in this interaction.

        The string returned from this method may not always end up being the
        string returned to the Eva clients. A plugin may end up modifying the
        output text at any point in the interaction (even right before sending
        the response to the client).

        :return: The output text for the Eva client so far in this interaction.
        :rtype: string
        """
        if self.output_text is None:
            return ''
        return self.output_text

    def get_input_audio(self):
        """
        Method used to get the input audio data that was sent by the client for
        this interaction.

        :return: The audio binary data received from an Eva client this interaction.
        :rtype: binary string
        """
        return self.input_audio

    def get_input_audio_content_type(self):
        """
        Method that returns the content type of the audio binary data received
        during this interaction.

        Typically something like 'audio/mpeg' or 'audio/wave'.

        :return: The content type of the audio binary data received this interaction.
        :rtype: string
        """
        return self.input_audio_content_type

    def get_output_audio(self):
        """
        Method that returns the resulting output audio binary data that the Eva
        client will play to the user.

        :return: The output audio binary data that Eva will send back to the client.
        :rtype: binary string
        """
        return self.output_audio

    def get_output_audio_content_type(self):
        """
        Method that returns the output audio content type that will be sent back
        to the Eva client.

        :return: The content type of the audio binary data returned to the Eva client.
        :rtype: string
        """
        return self.output_audio_content_type

    def response_ready(self):
        """
        Method used by plugins to determine whether or not they should take part
        in this current interaction.

        A response being ready means that another plugin has already set some
        output text that should be sent back to the Eva client.

        :return: True if a response has already been generated, False otherwise.
        :rtype: boolean
        """
        return self.responded

    def contains(self, keyword):
        """
        Simple helper method to determine if a keyword appears in a client's
        input text (query or command).

        :param keyword: The keyword to check for in the input text.
        :type param: string
        :return: True if the keyword is found, False otherwise.
        :rtype: boolean
        """
        return self.input_text is not None and keyword in self.input_text

    def set_input_text(self, text):
        """
        Method used to set the input text of the current interaction.

        This function is primarily used by voice recognition plugins to convert
        input audio into input text when clients don't provide any.

        This method fires the ``eva.pre_set_input_text`` and ``eva.post_set_input_text``
        triggers.

        :param text: The text that will now become the input text from the client.
        :type text: string
        """
        plugin = get_calling_plugin()
        gossip.trigger('eva.pre_set_input_text', text=text, plugin=plugin, context=self)
        self.input_text = text
        gossip.trigger('eva.post_set_input_text', text=text, plugin=plugin, context=self)

    def set_input_audio(self, audio, content_type):
        """
        Same as :func:`set_input_text` except it works for the input audio and
        content type. Not very many plugins will end up using this as it involves
        modifying the audio query or command that was sent by the Eva client.

        This method fires the ``eva.pre_set_input_audio`` and
        ``eva.post_set_input_audio`` triggers.

        :param audio: The audio to be set as the input audio for this interaction.
        :type audio: binary string
        :param content_type: The content type of this binary audio data.
        :type content_type: string
        """
        plugin = get_calling_plugin()
        gossip.trigger('eva.pre_set_input_audio',
                       audio=audio,
                       content_type=content_type,
                       plugin=plugin,
                       context=self)
        self.input_audio = audio
        self.input_audio_content_type = content_type
        gossip.trigger('eva.post_set_input_audio',
                       audio=audio,
                       content_type=content_type,
                       plugin=plugin,
                       context=self)

    def set_output_text(self, text, responding=True):
        """
        The bread and butter method of the context object.

        This method is used by nearly every plugin as it's used to tell Eva what
        the response to the client should be.

        This method fires the ``eva.pre_set_output_text`` and
        ``eva.post_set_output_text`` triggers.

        :param text: The text to be set as output for the client.
        :type text: string
        :param responding: ``True`` if the text provided is a response to the client.
            ``False`` if you're simply modifying the output text without claiming to be
            the primary plugin to respond to the query or command.

            Leaving this as ``True`` means other plugins will be able to tell that the
            client's query has already been answered (by checking the boolean variable
            returned by :func:`response_ready`).

            If a plugin is simply prepending/appending text or making slight
            modifications to the output, it should use ``responding=False`` so as to
            allow follow-up questions to be routed to the appropriate plugin.
        :type responding: boolean
        """
        plugin = get_calling_plugin()
        gossip.trigger('eva.pre_set_output_text',
                       text=text,
                       responding=responding,
                       plugin=plugin,
                       context=self)
        self.output_text = text
        self.responded = responding
        gossip.trigger('eva.post_set_output_text',
                       text=text,
                       responding=responding,
                       plugin=plugin,
                       context=self)

    def set_output_audio(self, audio, content_type):
        """
        Similar to :func:`set_output_text` except for the audio data and content
        type. This method will be used primarily by the text-to-speech plugins.

        :param audio: The audio binary data to send back to the client.
        :type audio: binary string
        :param content_type: The content type of the binary audio data.
        :type content_type: string
        """
        plugin = get_calling_plugin()
        gossip.trigger('eva.pre_set_output_audio',
                       audio=audio,
                       content_type=content_type,
                       plugin=plugin,
                       context=self)
        self.output_audio = audio
        self.output_audio_content_type = content_type
        gossip.trigger('eva.post_set_output_audio',
                       audio=audio,
                       content_type=content_type,
                       plugin=plugin,
                       context=self)

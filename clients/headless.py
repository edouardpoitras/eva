"""
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

* Requires that Eva have the
    `Audio Server <https://github.com/edouardpoitras/eva-audio-server>`_ plugin enabled

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
"""

import os
import time
import socket
import argparse
from threading import Thread, Event
from multiprocessing import Process
from respeaker.microphone import Microphone
from pymongo import MongoClient
from anypubsub import create_pubsub_from_settings
from pydub import AudioSegment
from pydub.playback import play as pydub_play

# Check for Snowboy.
try:
    import snowboy.snowboydecoder
except: #pylint: disable=W0702
    print('WARNING: Could not import Snowboy decoder/model - falling back to Pocketsphinx')

# Arguments passed via command line.
ARGS = None

# The sound played when Eva recognizes the keyword for recording.
PING_FILE = os.path.abspath(os.path.dirname(__file__)) + '/resources/ping.wav'
PONG_FILE = os.path.abspath(os.path.dirname(__file__)) + '/resources/pong.wav'

# Pocketsphinx/respeaker configuration.
os.environ['POCKETSPHINX_DIC'] = os.path.abspath(os.path.dirname(__file__)) + '/dictionary.txt'
os.environ['POCKETSPHINX_KWS'] = os.path.abspath(os.path.dirname(__file__)) + '/keywords.txt'

class DummyDecoder(object): #pylint: disable=R0903
    """
    Fake decoder in order to use respeaker's listen() method without setting
    up a pocketsphinx decoder.
    """
    def start_utt(self):
        """
        Overloaded method that simply passes.
        """
        pass


def listen(quit_event):
    """
    Utilizes respeaker's Microphone object to listen for keyword and sends audio
    data to Eva over the network once the keyword is heard.

    Audio data will be sent for a maximum of 5 seconds and will stop sending
    after 1 second of silence.

    :param quit_event: A threading event object used to abort listening.
    :type quit_event: :class:`threading.Event`
    """
    global ARGS
    global mic
    if ARGS.snowboy_model:
        mic = Microphone(quit_event=quit_event, decoder=DummyDecoder())
        while not quit_event.is_set():
            detector = snowboy.snowboydecoder.HotwordDetector(ARGS.snowboy_model, sensitivity=0.5)
            detector.start(detected_callback=handle_command,
                           interrupt_check=quit_event.is_set,
                           sleep_time=0.03)
            detector.terminate()
    else:
        mic = Microphone(quit_event=quit_event)
        while not quit_event.is_set():
            if mic.wakeup(ARGS.keyword):
                handle_command()

def handle_command():
    global mic
    play(PING_FILE)
    print('Listening...')
    data = mic.listen(duration=5, timeout=1)
    udp_stream(data)
    print('Done')
    play(PONG_FILE)

def play(filepath, content_type='audio/wav'):
    """
    Will attempt to play various audio file types (wav, ogg, mp3).
    """
    if 'wav' in content_type:
        sound = AudioSegment.from_wav(filepath)
    elif 'ogg' in content_type or 'opus' in content_type:
        sound = AudioSegment.from_ogg(filepath)
    elif 'mp3' in content_type or 'mpeg' in content_type:
        sound = AudioSegment.from_mp3(filepath)
    pydub_play(sound)

def udp_stream(data):
    """
    Simple helper function to send a generator type object containing audio
    data, over to Eva. Uses UDP as protocol.

    :param data: Generator type object returned from
        respeaker.microphone.Microphone.listen().
    :type data: Generator
    """
    global ARGS
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for d in data:
        udp.sendto(d, (ARGS.eva_host, ARGS.audio_port))
    udp.close()

def start_consumer(queue):
    """
    Starts a consumer to listen for pubsub-style messages on the specified
    queue. Will connect to a MongoDB server specified in the parameters.

    Uses multiprocessing.Process for simplicity.

    :param queue: The message queue to listen for messages on.
    :type queue: string
    """
    process = Process(target=consume_messages, args=(queue,))
    process.start()

def get_pubsub():
    """
    Helper function to get a anypubsub.MongoPubSub object based on parameters
    specified by command line. Will tail the 'eva' database's 'communications'
    collection for pubsub messages.

    :return: The anypubsub object used for receiving Eva messages.
    :rtype: anypubsub.backends.MongoPubSub
    """
    global ARGS
    uri = 'mongodb://'
    if len(ARGS.mongo_username) > 0:
        uri = uri + ARGS.mongo_username
        if len(ARGS.mongo_password) > 0: uri = uri + ':' + ARGS.mongo_password + '@'
        else: uri = uri + '@'
    uri = '%s%s:%s' %(uri, ARGS.mongo_host, ARGS.mongo_port)
    client = MongoClient(uri)
    return create_pubsub_from_settings({'backend': 'mongodb',
                                        'client': client,
                                        'database': 'eva',
                                        'collection': 'communications'})

def consume_messages(queue):
    """
    The worker function that is spawned in the :func:`start_consumer` function.
    Will do the work in listening for pubsub messages from Eva and playing
    the audio responses.

    :param queue: The pubsub message queue to subscribe to.
    :type queue: string
    """
    # Need to listen for messages and play audio ones to the user.
    pubsub = get_pubsub()
    subscriber = pubsub.subscribe(queue)
    # Subscriber will continuously tail the mongodb collection queue.
    for message in subscriber:
        if message is not None:
            if isinstance(message, dict) and \
               'output_audio' in message and \
               message['output_audio'] is not None:
                audio_data = message['output_audio']['audio']
                f = open('/tmp/eva_audio', 'wb')
                f.write(audio_data)
                f.close()
                play('/tmp/eva_audio', message['output_audio']['content_type'])
        time.sleep(0.1)

def main():
    """
    Parses client configuration options, starts the consumers, and starts
    listening for keyword.

    The keyword specified needs to be configured in respeaker (the keyword must
    be available in the pocketsphinx configuration for dictionary.txt and
    keywords.txt).
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--keyword", help="Keyword to listen for - only works if configured in dictionary.txt and keywords.txt", default='eva')
    parser.add_argument("--snowboy-model", help="Alternatively specify a Snowboy model instead of using Pocketsphinx for keyword detection")
    parser.add_argument("--eva-host", help="Eva server hostname or IP", default='localhost')
    parser.add_argument("--audio-port", help="Port that Eva is listening for Audio", default=8800)
    parser.add_argument("--mongo-host", help="MongoDB hostname or IP (typically same as Eva)", default='localhost')
    parser.add_argument("--mongo-port", help="MongoDB port", default=27017)
    parser.add_argument("--mongo-username", help="MongoDB username", default='')
    parser.add_argument("--mongo-password", help="MongoDB password", default='')
    global ARGS
    ARGS = parser.parse_args()
    # Start the message consumers.
    start_consumer('eva_messages')
    start_consumer('eva_responses')
    # Ready listening thread.
    quit_event = Event()
    thread = Thread(target=listen, args=(quit_event,))
    thread.start()
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            quit_event.set()
            break
    thread.join()

if __name__ == '__main__':
    main()

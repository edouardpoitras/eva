"""
Use this python client to send audio data and receive responses from Eva.

Requirements:
    - Requires a working pyaudio installation
        apt-get install portaudio19-dev
        apt-get install python-pyaudio
         or
        pip3 install pyaudio --user
    - Requires pocketsphinx, webrtcvad, respeaker
        apt-get install pocketsphinx
        pip3 install pocketsphinx webrtcvad respeaker
    - Requires pygame for audio playback
        apt-get install python3-pygame
         or
        pip3 install pygame --user
    - Requires anypubsub
        pip3 install anypubsub --user
    - Requires pymongo
        apt-get install python3-pymongo
         or
        pip3 install pymongo --user
    - Requires that Eva have the audio_server plugin enabled
"""
import os
import time
import socket
import argparse
from threading import Thread, Event
from multiprocessing import Process
from pygame import mixer
from pymongo import MongoClient
from respeaker.microphone import Microphone
from anypubsub import create_pubsub_from_settings

# Arguments passed via command line.
ARGS = None

# Pocketsphinx/respeaker configuration.
os.environ['POCKETSPHINX_DIC'] = os.path.abspath(os.path.dirname(__file__)) + '/dictionary.txt'
os.environ['POCKETSPHINX_KWS'] = os.path.abspath(os.path.dirname(__file__)) + '/keywords.txt'

def listen(quit_event):
    """
    Utilizes respeaker's Microphone object to liseen for keyword and sends audio
    data to Eva over the network once the keyword is heard.

    Audio data will be sent for a maximum of 5 seconds and will stop sending
    after 1 second of silence.

    :param quit_event: A threading event object used to abort listening.
    :type quit_event: :class:`threading.Event`
    """
    global ARGS
    mic = Microphone(quit_event=quit_event)
    while not quit_event.is_set():
        if mic.wakeup(ARGS.keyword):
            play('sound.wav')
            # Give the sound some time to play.
            time.sleep(0.5)
            print('Listening...')
            data = mic.listen(duration=5, timeout=1)
            udp_stream(data)
            print('Done')

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

def play(path):
    """
    Simple helper function to play an audio file at the specified path.
    Utilizes pygame.mixer to play audio files of various types.

    :param path: The path of the audio file on disk.
    :type path: string
    """
    mixer.init()
    mixer.music.load(path)
    mixer.music.play()

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
                play('/tmp/eva_audio')
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

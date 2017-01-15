"""
Use this python client to send audio data and receive responses from Eva.
Still needs a lot of work.

:todo: Clean it up, document better, and potentially replace a lot of this code
    with python's speech_recognition module.

Requirements:
    - Requires a working pyaudio installation
        apt-get install portaudio19-dev
        apt-get install python-pyaudio
         or
        pip3 install pyaudio --user
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
import socket
import struct
import math
import time
import pyaudio
from anypubsub import create_pubsub_from_settings
from pygame import mixer
from pymongo import MongoClient
from threading import Thread
from multiprocessing import Process

# Eva server hostname or IP.
HOST = 'localhost'
# Port for audio streaming - Eva expects 8800.
PORT = 8800
# Number of seconds to record a sample in order to get a threshold.
THRESHOLD_TEST_TIME = 3
# Percent loudness over normal ambient sound to count as speech.
THRESHOLD_MULTIPLIER = 2
# Number of seconds to wait on no audio to stop streaming to server.
MAX_IDLE_SECONDS = 1
SHORT_NORMALIZE = (1.0/32768.0)
# Audio rate for recording.
RATE = 16000
# Frames per buffer.
CHUNK = 1024

# Used to keep track of recorded frames to send across the network.
FRAMES = []

def get_rms(block):
    count = len(block) / 2
    fmt = "%dh" %count
    shorts = struct.unpack(fmt, block)
    sum_squares = 0.0
    for sample in shorts:
        n = sample * SHORT_NORMALIZE
        sum_squares += n * n
    return math.sqrt(sum_squares / count)

def get_threshold():
    # Prepare recording stream
    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)
    # Calculate the long run average, and thereby the proper threshold
    rms_values = []
    for _ in range(0, int(RATE / CHUNK * THRESHOLD_TEST_TIME)):
        block = stream.read(CHUNK)
        rms = get_rms(block)
        rms_values.append(rms)
    return sum(rms_values) / len(rms_values) * THRESHOLD_MULTIPLIER

def udp_stream():
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        if len(FRAMES) > 0:
            udp.sendto(FRAMES.pop(0), (HOST, PORT))
        time.sleep(0.01)

    udp.close()

def record():
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    print('Getting audio threshold level based on ambient noise...')
    threshold = get_threshold()
    print('Noise threshold set to %s' %threshold)
    idle_time = time.time()
    sending = False
    while True:
        try:
            block = stream.read(CHUNK)
        except IOError:
            pass
        amplitude = get_rms(block)
        if amplitude > threshold:
            print('Streaming audio...')
            sending = True
            FRAMES.append(block)
            idle_time = time.time()
        else:
            if sending:
                if time.time() - idle_time > MAX_IDLE_SECONDS:
                    print('Streaming stopped after inactivity')
                    sending = False

def play(path):
    mixer.init()
    mixer.music.load(path)
    mixer.music.play()

def start_consumer(queue):
    process = Process(target=consume_messages, args=(queue,))
    process.start()

def get_pubsub(host='localhost', port=27017, username='', password=''):
    uri = 'mongodb://'
    if len(username) > 0:
        uri = uri + username
        if len(password) > 0: uri = uri + ':' + password + '@'
        else: uri = uri + '@'
    uri = '%s%s:%s' %(uri, host, port)
    client = MongoClient(uri)
    return create_pubsub_from_settings({'backend': 'mongodb',
                                        'client': client,
                                        'database': 'eva',
                                        'collection': 'communications'})

def consume_messages(queue):
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

if __name__ == '__main__':
    start_consumer('eva_messages')
    start_consumer('eva_responses')
    recording_thread = Thread(target=record)
    streaming_thread = Thread(target=udp_stream)
    recording_thread.setDaemon(True)
    streaming_thread.setDaemon(True)
    recording_thread.start()
    streaming_thread.start()
    recording_thread.join()
    streaming_thread.join()

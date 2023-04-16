'''

#--- Steve Cox --- 1/10/19
# Copyright (c) Stef van der Struijk
# License: GNU Lesser General Public License

# Modified code to play sound from buffer recording
# Added code to wait till sound is finished play so no echo occurs

# Modification of:
# https://github.com/wiseman/py-webrtcvad (MIT Copyright (c) 2016 John Wiseman)
# https://github.com/wangshub/python-vad (MIT Copyright (c) 2017 wangshub)

Requirements:
+ pyaudio - `pip install pyaudio`
+ py-webrtcvad - `pip install webrtcvad`
'''
import webrtcvad
import collections
import sys
import signal
import pyaudio

from array import array
from struct import pack
import wave
import time

import asyncio

FORMAT = pyaudio.paInt16
CHANNELS = 1
SAMPLE_RATE = 16000
CHUNK_DURATION_MS = 30       # supports 10, 20 and 30 (ms)
PADDING_DURATION_MS = 1500   # 1 sec jugement
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION_MS / 1000)  # chunk to read
CHUNK_BYTES = CHUNK_SIZE * 2  # 16bit = 2 bytes, PCM
NUM_PADDING_CHUNKS = int(PADDING_DURATION_MS / CHUNK_DURATION_MS)

#--- Steve Cox
NUM_WINDOW_CHUNKS = int(240 / CHUNK_DURATION_MS)
#NUM_WINDOW_CHUNKS = int(400 / CHUNK_DURATION_MS)  # 400 ms/ 30ms  ge

NUM_WINDOW_CHUNKS_END = NUM_WINDOW_CHUNKS * 2
START_OFFSET = int(NUM_WINDOW_CHUNKS * CHUNK_DURATION_MS * 0.5 * SAMPLE_RATE)

#-----------------------------------------------------------------------------------------------------
def normalize(snd_data):
            "Average the volume out"
            MAXIMUM = 32767  # 16384
            times = float(MAXIMUM) / max(abs(i) for i in snd_data)
            r = array('h')
            for i in snd_data:
                r.append(int(i * times))
            return r
#-----------------------------------------------------------------------------------------------------
class pyVAD:
    def __init__(self):
        self.vad = webrtcvad.Vad(1)
        
        pa = pyaudio.PyAudio()
        self.stream = pa.open(format=FORMAT,
                         channels=CHANNELS,
                         rate=SAMPLE_RATE,
                         input=True,
                         start=False,
                         # input_device_index=2,
                         frames_per_buffer=CHUNK_SIZE)

        self.got_a_sentence = False

    # Call in (threaded) for loop to constantaly record and send snippents back,        
    def wave_loop(self):
    
             while True:
                 ring_buffer = collections.deque(maxlen=NUM_PADDING_CHUNKS)
                 triggered = False
                 voiced_frames = []
                 ring_buffer_flags = [0] * NUM_WINDOW_CHUNKS
                 ring_buffer_index = 0

                 ring_buffer_flags_end = [0] * NUM_WINDOW_CHUNKS_END
                 ring_buffer_index_end = 0
                 buffer_in = ''
                 # WangS
                 raw_data = array('h')
                 index = 0
                 start_point = 0
                 StartTime = time.time()
                 #Debug
                 #print("* recording: ")
                 self.stream.start_stream()

                 while not self.got_a_sentence:
                     chunk = self.stream.read(CHUNK_SIZE)
                     # add WangS
                     raw_data.extend(array('h', chunk))
                     index += CHUNK_SIZE
                     TimeUse = time.time() - StartTime
                     active = self.vad.is_speech(chunk, SAMPLE_RATE)

                     ring_buffer_flags[ring_buffer_index] = 1 if active else 0
                     ring_buffer_index += 1
                     ring_buffer_index %= NUM_WINDOW_CHUNKS

                     ring_buffer_flags_end[ring_buffer_index_end] = 1 if active else 0
                     ring_buffer_index_end += 1
                     ring_buffer_index_end %= NUM_WINDOW_CHUNKS_END

                     # start point detection
                     if not triggered:
                         ring_buffer.append(chunk)
                         num_voiced = sum(ring_buffer_flags)
                         if num_voiced > 0.8 * NUM_WINDOW_CHUNKS:
                             triggered = True
                             start_point = index - CHUNK_SIZE * 20  # start point
                             ring_buffer.clear()
                     # end point detection
                     else:
                         ring_buffer.append(chunk)
                         num_unvoiced = NUM_WINDOW_CHUNKS_END - sum(ring_buffer_flags_end)

                         if num_unvoiced > 0.90 * NUM_WINDOW_CHUNKS_END or TimeUse > 10:
                              triggered = False
                              self.got_a_sentence = True

                 #Debug
                 #print("* done recording")
                 self.stream.stop_stream()
                 #Don't close the stream so we can keep recording
                 #self.stream.close()
                 self.got_a_sentence = False

                 # tweak data
                 raw_data.reverse()
                 for index in range(start_point):
                     raw_data.pop()
        
                 raw_data.reverse()
                 raw_data = normalize(raw_data)
                 #--- Steve Cox: the wav has a header, we need to strip it off before playing
                 wav_data = raw_data[44:len(raw_data)]
                 yield wav_data
                

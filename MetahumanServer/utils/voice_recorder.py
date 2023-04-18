
import collections

from array import array
import wave
import time

import pyaudio
import webrtcvad

FORMAT = pyaudio.paInt16
CHANNELS = 1
SAMPLE_RATE = 16000
CHUNK_DURATION_MS = 30       # supports 10, 20 and 30 (ms)
PADDING_DURATION_MS = 1500   # 1 sec jugement
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION_MS / 1000)  # chunk to read
CHUNK_BYTES = CHUNK_SIZE * 2  # 16bit = 2 bytes, PCM
NUM_PADDING_CHUNKS = int(PADDING_DURATION_MS / CHUNK_DURATION_MS)

NUM_WINDOW_CHUNKS = int(240 / CHUNK_DURATION_MS)
#NUM_WINDOW_CHUNKS = int(400 / CHUNK_DURATION_MS)  # 400 ms/ 30ms  ge

NUM_WINDOW_CHUNKS_END = NUM_WINDOW_CHUNKS * 2
START_OFFSET = int(NUM_WINDOW_CHUNKS * CHUNK_DURATION_MS * 0.5 * SAMPLE_RATE)

def normalize(snd_data):
    "Average the volume out"
    MAXIMUM = 32767  # 16384
    times = float(MAXIMUM) / max(abs(i) for i in snd_data)
    r = array('h')
    for i in snd_data:
        r.append(int(i * times))
    return r

class VoiceRecorder:
    def __init__(self, vad_aggressivensess=1):
        self.vad = webrtcvad.Vad(vad_aggressivensess)
        
        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(format=FORMAT,
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
                #print("TimeUse: ", TimeUse, "speech active: ", active)

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
                        print("Recording: Segment START")
                        start_point = index - CHUNK_SIZE * 20  # start point
                        ring_buffer.clear()
                # end point detection
                else:
                    ring_buffer.append(chunk)
                    num_unvoiced = NUM_WINDOW_CHUNKS_END - sum(ring_buffer_flags_end)

                    if num_unvoiced > 0.50 * NUM_WINDOW_CHUNKS_END or TimeUse > 4:
                        triggered = False
                        print("Recording: Segment END")
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
            #print("yield wav_data")
            yield wav_data
            
import sys
from io import BytesIO

def main():
    vad = VoiceRecorder(3)
    
    print("Starting voice activity detection...")
    try:
        for wav_data in vad.wave_loop():
            print("Saving voice activity to a file...")
            with wave.open("voice_activity.wav", "wb") as wave_file:
                wave_file.setnchannels(CHANNELS)
                wave_file.setsampwidth(2)  # 16-bit samples
                wave_file.setframerate(SAMPLE_RATE)
                wave_file.writeframes(wav_data)
            print("Voice activity saved to 'voice_activity.wav'")
            break  # This is to record only one voice activity segment, remove this line to keep recording

    except KeyboardInterrupt:
        print("Interrupted, stopping...")
    finally:
        vad.stream.stop_stream()
        vad.stream.close()
        vad.pa.terminate()  # Call terminate() on the PyAudio object (pa) instead of the stream object
        print("Finished.")

if __name__ == "__main__":
    main()
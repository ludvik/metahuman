import json
#pip install pygame
import pygame
#pip install pyaudio
import pyaudio
import wave
import glob
import time

import io
import os
from _datetime import datetime;


# Imports the Google Cloud client library
#pip install google-cloud-speech
from google.cloud import speech

#pip install google-cloud-texttospeech
from google.cloud import texttospeech

from google.auth.credentials import Credentials

# Constants
FORMAT = pyaudio.paInt16
CHANNELS = 1
SAMPLE_RATE =  16000          #44100
CHUNK = 1024
RECORD_SECONDS = 3

class GoogleSpeech:
    def __init__(self):
        
        # Instantiates a speechRecognition_client

        self.speech_client = speech.SpeechClient()

        # config our google speech/text recognition engine
        self.config = speech.RecognitionConfig(encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,sample_rate_hertz=SAMPLE_RATE,language_code='en-US')
        self.texttospeech_client = texttospeech.TextToSpeechClient()
        self.texttospeech_voice = texttospeech.VoiceSelectionParams(language_code='en-US',ssml_gender=texttospeech.SsmlVoiceGender.FEMALE)
        self.texttospeech_audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.LINEAR16)


    def SpeechToText(self,wav_data):

        audio = speech.RecognitionAudio(content=bytes(wav_data))

        response = self.speech_client.recognize(config=self.config,audio=audio)

        # For each response, send to chat bot
        speech_to_text = "Nothing"
        for result in response.results:
            speech_to_text = result.alternatives[0].transcript
            
        return speech_to_text

    def TextToSpeech(self,text_to_convert):
        input_text = texttospeech.types.SynthesisInput(text=text_to_convert)
        # need to convert this to a wave
        response_object = self.texttospeech_client.synthesize_speech(input_text, self.texttospeech_voice, self.texttospeech_audio_config)
        #--- Steve Cox: the wav has a header, we need to strip it off before playing or you here a click
        raw_data = response_object.audio_content
        wav_data = raw_data[44:len(raw_data)]
        return wav_data

    def TextToSpeech_Raw(self,text_to_convert):
        input_text = texttospeech.types.SynthesisInput(text=text_to_convert)
        # need to convert this to a wave
        response_object = self.texttospeech_client.synthesize_speech(input_text, self.texttospeech_voice, self.texttospeech_audio_config)
        return response_object.audio_content
        
if __name__ == '__main__':

    pa = pyaudio.PyAudio()

    for i in range(pa.get_device_count()):
        dev_info = pa.get_device_info_by_index(i)
        print(f"Device {i}: {dev_info['name']} (input channels: {dev_info['maxInputChannels']}, output channels: {dev_info['maxOutputChannels']})")

    pa.terminate()
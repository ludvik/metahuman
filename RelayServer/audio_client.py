import json
import time

import io
import os

import asyncio
import socketio
import random

from utils.pyVAD_utils import pyVAD
from utils.GoogleSpeechAPI import GoogleSpeech

#from gpt3_chat_utils import ask , append_interaction_to_chat_log , chat_log
from utils.openai_utils import ask_chatGPT


sio = socketio.AsyncClient()

@sio.event
async def connect():
    print('connection established')

@sio.event
async def chatMessage(data):
    #print('chatMessage received with ', data)
    #await sio.emit('my response', {'response': 'my response'})
    pass
#-----------------------------------------------------------------------
@sio.event
async def disconnect():
    print('disconnected from server')



# The file we keep all our conversations in during this chat session
#thenow = datetime.now().strftime("%Y%m%d%H%M%S")
#sessionFileName = "session_data_" + thenow + ".txt"

print('-------------------------------- Say something -----------------------------------')


#---------------------------------------------------------------------------------------
async def main():

    #--- Steves google speech wrapper
    speech = GoogleSpeech()

    #--- Steve etl VAD class    
    py_VADx = pyVAD()

    chat_log = ''

    await sio.connect('http://localhost:3000')

    while True:

        for wav_data in py_VADx.wave_loop():
        
            #--- Send to Google and get speech to text 
            converted_text = speech.SpeechToText(wav_data)
            
            #--- Noise sometimes comes back, so speech lib returns "Nothing" 
            if not converted_text == 'Nothing':
        
                #answer = ask(converted_text, chat_log)
                #chat_log = append_interaction_to_chat_log(converted_text, answer, chat_log)
                chatgpt_response = ask_chatGPT(converted_text)
                print(chatgpt_response)
                #say_this = f"say_{answer.strip()}"
                say_this = f"say_{chatgpt_response}"
                await sio.emit('chatMessage', say_this)
                await sio.sleep(1) #random.randint(1, 3))

if __name__ == '__main__':
    asyncio.run(main())

    


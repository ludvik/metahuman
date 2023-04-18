import os
import asyncio
import socketio
import tempfile
import wave

from utils.voice_recorder import VoiceRecorder
from utils.openai_util import ask_chatGPT, speech_to_text

CHANNELS = 1
SAMPLE_RATE = 16000

def save_wavefile(wave_data, file_path):
    try:
        with wave.open(file_path, "wb") as tmp_wave_file:
            tmp_wave_file.setnchannels(CHANNELS)
            tmp_wave_file.setsampwidth(2)  # 16-bit samples
            tmp_wave_file.setframerate(SAMPLE_RATE)
            tmp_wave_file.writeframes(wave_data)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        tmp_wave_file.close()
    return tmp_wave_file
    

print('-------------------------------- Say something -----------------------------------')
async def main():

    py_VADx = VoiceRecorder(2)
    sio = socketio.AsyncClient()

    await sio.connect('http://127.0.0.1:3000')
    while True:
        try:
            for wav_data in py_VADx.wave_loop():
                #--- Save wav_data to a temporary file
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                    with wave.open(tmp_file.name, "wb") as wave_file:
                        wave_file.setnchannels(CHANNELS)
                        wave_file.setsampwidth(2)  # 16-bit samples
                        wave_file.setframerate(SAMPLE_RATE)
                        wave_file.writeframes(wav_data)

                try:
                    #--- Send to OpenAI Speech API and get speech to text
                    with open(tmp_file.name, "rb") as audio_file:
                        converted_text = speech_to_text(audio_file)

                    #--- Noise sometimes comes back, so speech lib returns "Nothing" 
                    if converted_text != 'Nothing':
                        chatgpt_response = ask_chatGPT(converted_text)
                        print(chatgpt_response)
                        say_this = f"say_{chatgpt_response}"
                        await sio.emit('chatMessage', say_this)
                        await sio.sleep(1) #random.randint(1, 3))

                finally:
                    #--- Delete the temporary file
                    os.remove(tmp_file.name)

        except Exception as e:
            print(f"An error occurred: {e}")

        finally:
            await sio.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
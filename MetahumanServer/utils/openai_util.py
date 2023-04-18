import os
import io
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

message_log = [
         {"role": "system", "content": "You are a heartfelt receiptionist. You work for an airbnb house owner located in the city of San Jose. This is a 3 bed lovely single house with a very large backyard, suitable for families with children or hold party. Your responsibility is to on boarding new guests. Answer any questions about the house. And gently refuse any other questions irrelavent. You speak english only."},
         {"role": "user", "content": "Hi, there!"},
       ]

#------------------------------------------------------------------------------------------
def ask_chatGPT(user_input): 

    global message_log

    new_record = {"role": "user", "content": f"{user_input}" }
    message_log.append(new_record)

    response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", 
            messages=message_log,
            temperature = 0.3,
            max_tokens  = 100           
            )
    
    answer = response['choices'][0]['message']['content']
    new_record = {"role": "assistant", "content": f"{answer}"}
    message_log.append(new_record)

    return answer

def speech_to_text(wav_file):
    try:
        print("Transcribing...")
        response = openai.Audio.transcribe(model="whisper-1", file=wav_file)
    except Exception as e:
        print(f"An error occurred while calling OpenAI Speech to Text API: {e}")
        return 'Nothing'

    transcript = response["text"]
    return transcript.strip()

#------------------------------------------------------------------------------------------
# Main
#------------------------------------------------------------------------------------------
def main():

    while True:
        user_input = input("Type something to Ada: ")
        if user_input == "quit" or user_input == "q":
            break

        answer = ask_chatGPT(user_input)
        print(answer)

def test_speech_to_text():
    # Pass the wave file to the speech_to_text function
    with open("voice_activity.wav", "rb") as file:
        transcript = speech_to_text(file)

    print("Transcript:", transcript)

if __name__ == '__main__':
    # Call the test function
    test_speech_to_text()


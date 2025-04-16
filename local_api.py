
from gtts import gTTS
import datetime
import os
import whisper
from helper import get_audio_folder, logger_service
def local_asr(audio_file_path: str, language: str) -> str:
    try:
        # Load the Whisper model
        model = whisper.load_model("small")
        # Transcribe the audio file with float parameters
        print(language[0:2])
        response = model.transcribe(
            audio_file_path, 
            task="transcribe", 
            language=language[0:2], 
            temperature=0,
            fp16=False,  
            initial_prompt="This is a conversation about banking services."
        )
        if response is not None:
            if response["text"] is None:
                return ""    
            return response["text"]
        else:
            return ""
    except Exception as e:
        logger_service("Whisper model error:", e)
        return ""
    

def local_tts(text: str, language: str) -> None:
    try:
        # Define the text to be synthesized
        # Initialize the TTS engine
        tts = gTTS(text=text, lang=language[0:2])
            
        # Save the speech to an audio file
        current_time = datetime.datetime.now()
        file_path = get_audio_folder(current_time)
        file_name = current_time.strftime('%H%M%S-teller')+".wav"   
        full_audio_file = file_path.replace('/','.') + '.'+ file_name
        tts.save(file_path + '/'+ file_name)
        return full_audio_file
    except Exception as e:
        logger_service("gTTS error:", e)
        return ""
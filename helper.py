import datetime
import os
import json
import torch
from googletrans import Translator

audio_folder = "audio"
def check_and_create_folder(folder_path=audio_folder):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Folder '{folder_path}' created.")

def get_audio_folder(current_time: datetime):
    subfolder = current_time.strftime('%Y%m%d')
    full_folder = audio_folder +'/'+ subfolder
    check_and_create_folder(full_folder)
    return full_folder

def serialize_json_object(jsonObj: dict):
    if (jsonObj is None):
        return ""
    try:
        ret = json.dumps(jsonObj)
        return ret
    except Exception as error:
        print("serialize_json_object", error)
        return ""
    
async def translate_text_english(input_text, src_language):
    try:
        # Initialize the Translator
        translator = Translator()

        # Perform translation asynchronously
        translated = await translator.translate(input_text, src=src_language, dest="en")
        return translated.text  # Ensure we access the 'text' attribute of the result
    except Exception as e:
        print(f"translate_text_googletrans: An error occurred: {e}")
        return ""

def check_cuda_support():
    if torch.cuda.is_available():
        return "cuda"
    else:
        return "cpu"
    
def logger(*args):
    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), end=" ")
    if len(args) == 0:
        return
    for arg in args:
        if isinstance(arg, dict):
            print(json.dumps(arg, ensure_ascii=False))
        else:
            print(arg)
    return

    
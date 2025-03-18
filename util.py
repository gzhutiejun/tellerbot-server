import datetime
import os

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
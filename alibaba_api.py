
import datetime
import os

from fastapi import logger
import requests

def send_audio_and_get_text(audio_file_path: str, app_key: str, token: str, url: str = "https://nls-gateway-cn-shenzhen.aliyuncs.com/stream/v1/asr") -> str:
    """
    Send audio data to the NLS service and get the recognized text.

    Args:
        audio_file_path (str): Path to the audio file.
        app_key (str): Application key for NLS.
        token (str): Authentication token for NLS.
        url (str): NLS service endpoint URL.

    Returns:
        str: Recognized text from the audio.
    """
    if not os.path.exists(audio_file_path):
        raise FileNotFoundError("Audio file not found")

    headers = {
        "X-NLS-Token": token,
        "Content-Type": "application/octet-stream",
        "Host": "nls-gateway-cn-shenzhen.aliyuncs.com",
    }
    params = {
        "appkey": app_key,    
    }

    try:
        print(audio_file_path)
        with open(audio_file_path, "rb") as audio_file:
            data = audio_file.read()
            response = requests.post(url, headers=headers, params=params, data=data)
            res = response.json()
            if res.get("code") != 200:
                return res["result"]
            else:
                return ""
        
        response.raise_for_status()
        return response.json().get("result", "")
    except requests.exceptions.RequestException as e:
        logger("Request failed:", e)
        return ""

# ali_app_key = "yWFqGNJUecDlp3pF"
# ali_token = "c698ef856c97440bb1780e7de61e1bc8"

# result = send_audio_and_get_text("./audio/20250413/output1.wav",ali_app_key,ali_token)
# print(result)


import datetime
import os

import requests

from helper import get_audio_folder, logger_service

def ali_asr(audio_file_path: str, app_key: str, token: str, url: str = "https://nls-gateway-cn-shenzhen.aliyuncs.com/stream/v1/asr") -> str:
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
                return None
        
        response.raise_for_status()
        return response.json().get("result", "")
    except requests.exceptions.RequestException as e:
        logger_service("Request failed:", e)
        return None

def ali_tts(text: str, app_key: str, token: str, url: str = "https://nls-gateway-cn-shenzhen.aliyuncs.com/stream/v1/tts") -> None:
    """
    Send text to the NLS service for TTS synthesis.

    Args:
        text (str): Text to be synthesized.
        app_key (str): Application key for NLS.
        token (str): Authentication token for NLS.
        url (str): NLS service endpoint URL.
    """
    headers = {
        "X-NLS-Token": token,
        "Content-Type": "audio/mpeg",
        "Host": "nls-gateway-cn-shenzhen.aliyuncs.com",
    }
    params = {
        "appkey": app_key,
        "text": text,
        "format": "wav",
        "sample_rate": 16000,
    }

    response = requests.post(url, headers=headers, params=params)
    if response.status_code == 200:
        logger_service("Request succeeded:")
        current_time = datetime.datetime.now()
        file_path = get_audio_folder(current_time)
        file_name = current_time.strftime('%H%M%S-teller')+".wav"
        full_audio_file = file_path.replace('/','.') + '.'+ file_name

        with open(file_path + '/'+ file_name, "wb") as audio_file:
            audio_file.write(response.content)
            return full_audio_file
    else:
        logger_service("Request failed:", response.text)
        return ""


# ali_token = os.environ.get("ALI_TOKEN")
# ali_asr1_app_key = os.environ.get("ALI_ASR1_APPKEY")
# ali_asr2_app_key = os.environ.get("ALI_ASR2_APPKEY")
# print(ali_token,ali_asr1_app_key,ali_asr2_app_key)
# res = ali_tts("您好，请问您需要什么服务？", ali_asr1_app_key, ali_token)
# print(res)

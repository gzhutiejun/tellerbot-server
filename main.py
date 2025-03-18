# main.py

import datetime
from ollama import chat
import uuid
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from transformers import pipeline
from gtts import gTTS
import os

from model import getJsonSchema
from util import check_and_create_folder

check_and_create_folder()

app = FastAPI()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return "teller chatbot service"

@app.get("/status/")
async def root():
    return {"success": True}

@app.post("/opensession/")
async def open_session(req: dict) -> dict:
    id: uuid.UUID = uuid.uuid1()
    return {
        "success": True,
        "session_id": id
    }

@app.post("/closesession/")
async def close_session(req: dict) -> dict:
    id = None
    if "session_id" in req:
        id = req['session_id']
    print(id)
    return {
        "success": True,
        "session_id": id
    }

@app.post("/extract/")
async def extract(req: dict) -> dict:
    result = {
        "success": False,
        "reason": ""
    }

    if req is None or 'schema' not in req or 'text' not in req:
        result['reason'] = "parameter is invalid"
        return result
    
    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') +" start " + req['action'])

    text = req['text']
    schema = req['schema']

    try:
        # Get the extracted data
        response = chat(
            model="llama3.2",
            messages=[
                {
                    "role": "user",
                    "content": text,
                },
                {
                    "role": "user",
                    "content": "set property 'answer' to true if %{text} contains yes",
                },
                {
                    "role": "user",
                    "content": "set property 'cancelled' to true if %{text} contains cancel or exit, otherwise set to false",
                }
            ],
            format= getJsonSchema(schema)
        )
        result['success'] = True
        result['data'] = response.message.content
    except Exception as error:
        print("exception occurs", error)
        raise HTTPException(status_code=500, detail='Something went wrong')
    
    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') +" complete " + req['action'])
    return result

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    current_time = datetime.datetime.now()
    full_file_path = get_audio_folder(current_time) + '/' + current_time.strftime('%H%M%S-customer')+".mp3"
    
    try:
        with open(full_file_path, 'wb') as f:
            while contents := file.file.read(1024 * 1024):
                f.write(contents)
    except Exception as error:
        print("exception occurs", error)
        raise HTTPException(status_code=500, detail='Something went wrong')
    finally:
        file.file.close()
    return {"success": True, "file_path": full_file_path.replace('/','.')}

@app.get("/download/{file_path}")
async def download_file(file_path: str, range: str = None) -> StreamingResponse:
    print("download", file_path)

    if file_path is None:
        raise HTTPException(status_code=404, detail="File not found")

    file_path_full = ""
    try:    
        temp = file_path.split('.')
        file_path_full = './' + temp[0] + '/' + temp[1]+ '/'+ temp[2] + '.' + temp[3]
    except:
        raise HTTPException(status_code=404, detail="File not found")
    
    if not os.path.exists(file_path_full) or file_path is None:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_size = os.path.getsize(file_path_full)
    headers = {"Accept-Ranges": "bytes"}

    def file_stream(start: int, end: int):
        with open(file_path_full, "rb") as f:
            f.seek(start)
            while start < end:
                chunk_size = min(1024 * 1024, end - start)
                data = f.read(chunk_size)
                if not data:
                    break
                start += len(data)
                yield data

    if range:
        try:
            range_start, range_end = range.replace("bytes=", "").split("-")
            range_start = int(range_start) if range_start else 0
            range_end = int(range_end) if range_end else file_size - 1
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid range header")

        if range_start >= file_size or range_end >= file_size or range_start > range_end:
            raise HTTPException(status_code=416, detail="Requested Range Not Satisfiable")

        headers.update({
            "Content-Range": f"bytes {range_start}-{range_end}/{file_size}",
            "Content-Length": str(range_end - range_start + 1),
        })
        return StreamingResponse(file_stream(range_start, range_end + 1), headers=headers, status_code=206)

    headers["Content-Length"] = str(file_size)
    return StreamingResponse(file_stream(0, file_size), headers=headers)

@app.post("/transcribe/")
async def transcribe(req: dict) -> dict:
    result = {
        "success": False,
        "reason": "",
    }
    
    if req is None or 'action' not in req or "file_path" not in req:
        result['reason'] = "parameter is invalid"
        return result
    
    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') +" start " + req['action'])

    file_path = req['file_path']
    if file_path is None:
        raise HTTPException(status_code=404, detail="File not found")

    file_path_full = ""
    try:    
        temp = file_path.split('.')
        print('temp', temp)

        file_path_full = './' + temp[0] + '/' + temp[1]+ '/'+ temp[2] + '.' + temp[3]
    except:
        raise HTTPException(status_code=404, detail="File not found")
    
    if not os.path.exists(file_path_full) or file_path is None:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        # Load the pipeline for automatic speech recognition (ASR)
        asr_pipeline = pipeline(task="automatic-speech-recognition", model="openai/whisper-small")

        # Perform the transcription
        response = asr_pipeline(file_path_full)
        if response is not None:
            result['success'] = True
            result['transcript'] = response["text"]
    except Exception as error:
        result['reason'] = "exception"
        print("exception occurs", error)
        raise HTTPException(status_code=500, detail='Something went wrong')

    # Print the transcribed text
    #print("Transcribed text:", result["text"])
    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') +" complete " + req['action'])
    return result

@app.post("/generateaudio/")
async def generate_audio(req: dict) -> dict:
    result = {
        "success": False,
        "reason": "",
    }

    if req is None or 'action' not in req or "text" not in req:
        result['reason'] = "parameter is invalid"
        return result
    
    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') +" start " + req['action'])

    try:
        # Define the text to be synthesized
        text = req['text']
        lang = req['lang'] if 'lang' in req else 'en'
        # Initialize the TTS engine
        tts = gTTS(text=text, lang=lang)
        
        # Save the speech to an audio file
 
        result['success'] = True
        current_time = datetime.datetime.now()
        file_path = get_audio_folder(current_time)
        file_name = current_time.strftime('%H%M%S-teller')+".mp3"
        result['file_name'] = file_path.replace('/','.') + '.'+ file_name

        tts.save(file_path + '/'+ file_name)
    except Exception as error:
        result['reason'] = "exception"
        print("exception occurs", error)
        raise HTTPException(status_code=500, detail='Something went wrong')

    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') +" complete " + req['action'])
    return result
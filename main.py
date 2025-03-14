# main.py

import datetime
import uuid
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from transformers import pipeline
from gtts import gTTS
import os

llm = ChatOpenAI(
    api_key="ollama",
    model="llama3.2",
    base_url="http://localhost:11434/v1/",
    temperature=0,
    max_tokens=2000,
)

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

    if req is None or not 'action' in req or not 'template' in req or not 'format' in req or not 'text' in req:
        result['reason'] = "parameter is invalid"
        return result
    
    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') +" start " + req['action'])
    '''
    text_message = "I want to withdraw 600 hong kong dollars from my saving account, and print receipt"

    # Define the messages for extraction
    messages = [
        ("system", "You are a helpful assistant that extracts data from text messages and Always answer in the following json format: {json_data_format}"),
        ("human", f"Extract data from the following text message, including number or amount, currency, account type, transaction type and if receipt is required: {text_message}")
    ]
    
    '''
    if req is None:
        return {
            "success": False,
            "reason": "req is empty"
        }
    dataFormat = req['format']
    text = req['text']
    template = req['template']
    message = [
        ("system", f"You are a helpful assistant that extracts data from text messages and always answer in the following json format: {dataFormat}"),
        ("human", f"{template}: {text}")
    ]

    if dataFormat is None or text is None or template is None or message is None:
        result['reason'] = "parameter is invalid"
        return result
    
    try:
        # Get the extracted data
        response = llm.invoke(message)
        result['success'] = True
        result['data'] = response.content
    except Exception as error:
        print("exception occurs", error)
        raise HTTPException(status_code=500, detail='Something went wrong')
    
    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') +" complete " + req['action'])
    return result

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    filename ="./data/" + datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+".mp3"
    try:
        with open(filename, 'wb') as f:
            while contents := file.file.read(1024 * 1024):
                f.write(contents)
    except Exception as error:
        print("exception occurs", error)
        raise HTTPException(status_code=500, detail='Something went wrong')
    finally:
        file.file.close()
    return {"success": True, "file_path": filename}

@app.get("/download/{file_path}")
async def download_file(file_path: str) -> FileResponse:
    print("download",file_path)
    if os.path.exists("./data/" + file_path):
        return FileResponse(path="./data/" + file_path, filename="teller.mp3")
    else:
        raise HTTPException(status_code=404, detail="File not found")


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

    try:
        # Load the pipeline for automatic speech recognition (ASR)
        asr_pipeline = pipeline(task="automatic-speech-recognition", model="openai/whisper-small")

        # audio_file = "./data/cwd.wav"
        audio_file = req['file_path']

        # Perform the transcription
        response = asr_pipeline(audio_file)
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
        file_name = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+".mp3"
        result['file_name'] = file_name
        tts.save("./data/" + file_name)
    except Exception as error:
        result['reason'] = "exception"
        print("exception occurs", error)
        raise HTTPException(status_code=500, detail='Something went wrong')

    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') +" complete " + req['action'])
    return result
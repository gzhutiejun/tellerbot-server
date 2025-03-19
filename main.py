# main.py

import datetime
import uuid
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from gtts import gTTS
import os
import whisper
from langchain_openai import ChatOpenAI

from util import check_and_create_folder, get_audio_folder, serialize_json_object

llm = ChatOpenAI(
    api_key="ollama",
    model="llama3.2",
    base_url="http://localhost:11434/v1/",
    temperature=0,
    max_tokens=2000,
)

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

    if req is None or 'format' not in req or 'text' not in req or 'instruction' not in req:
        result['reason'] = "parameter is invalid"
        return result
    
    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " start " + req['action'])

    text = req['text']
    format = req['format']
    json_format = serialize_json_object(format)
    instruction = req['instruction']
    print(text)
    try:
        # Define the messages for extraction
        messages = [
            ("system", f"You are ChatOpenAI, a helpful assistant. Your task is to extract structured data from user messages. "
                       f"Your task is to extract information from user-provided text and oAlways respond with the extracted data in a JSON format as {json_format}"),
            ("human", f"Here is the instruction: {instruction}; if cancel or exit, set cancel property to true; If there is no mentioned data, return null. Extract the data from the following text: {text}" )
        ]

        # Get the extracted data
        response = llm.invoke(messages)
        print(response)
        result['success'] = True
        result['data'] = response.content
    except Exception as error:
        print("exception occurs", error)
        raise HTTPException(status_code=500, detail='Something went wrong')
    
    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " complete " + req['action'])
    return result

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    current_time = datetime.datetime.now()

    #if not file.content_type.startswith("audio/"):
        #raise HTTPException(status_code=400, detail="Invalid file type. Only audio files are allowed.")
    
    full_file_path = get_audio_folder(current_time) + '/' + current_time.strftime('%H%M%S-customer')+".webm"
    print("file size:",file.size)
    try:
        with open(full_file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
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
        file_path_full = './' + temp[0] + '/' + temp[1]+ '/'+ temp[2] + '.' + temp[3]
        if not os.path.exists(file_path_full) or file_path is None:
            raise HTTPException(status_code=404, detail="File not found")
    except:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        # Load the pipeline for automatic speech recognition (ASR)
        # asr_pipeline = pipeline(task="automatic-speech-recognition", model="openai/whisper-small")
        # Perform the transcription
        # response = asr_pipeline(file_path_full)
        
        # Load the Whisper model
        model = whisper.load_model("small")
        # Transcribe the audio file
        response = model.transcribe(file_path_full, fp16=False, language="en",temperature=1)
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
        file_name = current_time.strftime('%H%M%S-teller')+".webm"
        result['file_name'] = file_path.replace('/','.') + '.'+ file_name

        tts.save(file_path + '/'+ file_name)
    except Exception as error:
        result['reason'] = "exception"
        print("exception occurs", error)
        raise HTTPException(status_code=500, detail='Something went wrong')

    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') +" complete " + req['action'])
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
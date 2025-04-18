# main.py

import datetime
import uuid
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, UploadFile, HTTPException, logger
from fastapi.responses import StreamingResponse
import os

# from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama

from helper import check_and_create_folder, check_cuda_support, get_audio_folder, serialize_json_object, translate_text_english, logger_service

from alibaba_api import ali_asr, ali_tts
from local_api import local_asr, local_tts

use_local_api = True
ali_token = os.environ.get("ALI_TOKEN")
ali_asr1_app_key = os.environ.get("ALI_ASR1_APPKEY")
ali_asr2_app_key = os.environ.get("ALI_ASR2_APPKEY")
# openai approach
# llm = ChatOpenAI(
#     api_key="ollama",
#     model="llama3.2",
#     base_url="http://localhost:11434/v1/",
#     temperature=0,
#     max_tokens=2000,
# )

#ollama approach
local_llm_name = "llama3.2"
llm = ChatOllama(model=local_llm_name, temperature=0, format="json")

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
    logger_service(id)
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

    if req is None or 'schema' not in req or 'text' not in req or 'instruction' not in req:
        result['reason'] = "parameter is invalid"
        return result
    
    logger_service( "extract start")
    text = req['text']
    schema = req['schema']
    instruction = req['instruction']
    language = req['language'] if 'language' in req else 'en'
    user_text = text
    if (language != "en"):
        user_text = await translate_text_english(text, "zh-cn")

    logger_service("user_text",user_text)    
    if (user_text != None and (user_text.lower().find("cancel") >= 0 or user_text.lower().find("exit") >= 0 or user_text.lower().find("no need") >= 0)):
        result['success'] = True
        result['data'] = {"cancel": True}
        return result
    try:

        # Define the messages for extraction
        messages = [
            ("system", f"You are a helpful assistant. "
                    f"Your task is to extract structured data from user messages and only respond with JSON object as {serialize_json_object(schema)}"),
            ("human", "Extract following data:"
             f"{instruction}"
             f"Text: {user_text}")
        ]

        # Get the extracted data
        # response = llm.invoke(messages)
        response = llm.invoke(messages)
        result['success'] = True
        result['data'] = response.content
    except Exception as error:
        logger_service("exception occurs", error)
        raise HTTPException(status_code=500, detail='Something went wrong')
    
    logger_service( "extract complete ")
    return result

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    logger_service("upload start")
    current_time = datetime.datetime.now()

    full_file_path = get_audio_folder(current_time) + '/' + current_time.strftime('%H%M%S-customer')+".wav"
    try:
        with open(full_file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
    except Exception as error:
        logger_service("exception occurs", error)
        raise HTTPException(status_code=500, detail='Something went wrong')
    finally:
        file.file.close()
    logger_service("upload complete")
    return {"success": True, "file_path": full_file_path.replace('/','.')}

@app.get("/download/{file_path}")
async def download_file(file_path: str, range: str = None) -> StreamingResponse:
    logger_service("download", file_path)

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
    
    if req is None or "file_path" not in req:
        result['reason'] = "parameter is invalid"
        return result
    
    logger_service( "transcribe start")

    file_path = req['file_path']

    language = req['language'] if 'language' in req else 'en'
    ali_asr_app_key = ali_asr1_app_key
    if language.lower() == "zh-hk":
        ali_asr_app_key = ali_asr2_app_key

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
        text = None
        if use_local_api:
            text = local_asr(file_path_full, language)
        else:
            text = ali_asr(file_path_full, ali_asr_app_key, ali_token)
        if text is not None:
            result['success'] = True
            result['transcript'] = text
            logger_service("transcript output", text)
        else:
            result['reason'] = "transcription failed"
    except Exception as error:
        result['reason'] = "exception"
        logger_service("exception occurs", error)
        raise HTTPException(status_code=500, detail='Something went wrong')

    logger_service( "transcribe complete")
    return result

@app.post("/generateaudio/")
async def generate_audio(req: dict) -> dict:
    result = {
        "success": False,
        "reason": "",
    }

    if req is None or "text" not in req:
        result['reason'] = "parameter is invalid"
        return result
    
    logger_service( "generateaudio start ")

    try:
        # Define the text to be synthesized
        text = req['text']
        language = req['language'] if 'language' in req else 'en'
        ali_asr_app_key = ali_asr1_app_key
        if language.lower() == "zh-hk":
            ali_asr_app_key = ali_asr2_app_key

        logger_service(language)
        
        file_name = ""
        if use_local_api:
            file_name = local_tts(text, language)
        else:
            file_name = ali_tts(text, ali_asr_app_key, ali_token)
        if file_name is not None:
            result['success'] = True
            result['file_name'] = file_name
        else:
            result['reason'] = "audio generation failed"
    except Exception as error:
        result['reason'] = "exception"
        logger_service("exception occurs", error)
        raise HTTPException(status_code=500, detail='Something went wrong')

    logger_service("generateaudio complete ")
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
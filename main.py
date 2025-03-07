# main.py

import orjson
import datetime
from fastapi import FastAPI
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from transformers import pipeline


llm = ChatOpenAI(
    api_key="ollama",
    model="llama3.2",
    base_url="http://localhost:11434/v1/",
    temperature=0,
    max_tokens=2000,
)


json_data_format = orjson.dumps({
  "amount": 0,
  "currency": '',
  "accountType": '',
  "transactionType": '',
  "receiptRequired": False
})

app = FastAPI()

@app.get("/")
async def root():
    return "teller chatbot service"

@app.post("/extract/")
async def extract(req: dict) -> dict:

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
        return {
            "success": False,
            "reason": "some parameter is empty"
        }
    
    result = {
        "success": False,
        "reason": ""
    }
    try:
        # Get the extracted data
        response = llm.invoke(message)
        result['success'] = True
        result['text'] = response.content
    except:
        print("exception occurs")
        return {
            "success": False,
            "reason": "exception occurs"
        }
    
    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') +" complete " + req['action'])
    return result

@app.post("/transcribe/")
async def transcribe(req: dict) -> dict:
    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') +" start " + req['action'])
    # Load the pipeline for automatic speech recognition (ASR)
    asr_pipeline = pipeline(task="automatic-speech-recognition", model="openai/whisper-small")

    # Path to the audio file
    audio_file = "./data/cwd.wav"

    result = {
        "success": False,
        "reason": ""
    }
    try:
        # Perform the transcription
        response = asr_pipeline(audio_file)
        if response is not None:
            result['success'] = True
            result['text'] = response["text"]
    except:
        result['reason'] = "exception"
        print("exception occurs")

    # Print the transcribed text
    #print("Transcribed text:", result["text"])
    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') +" complete " + req['action'])
    return result
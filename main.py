# main.py

import orjson
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
async def extract(req: dict):
    
    print(req['action'])
    '''
    text_message = "I want to withdraw 600 hong kong dollars from my credit account, and print receipt"

    # Define the messages for extraction
    messages = [
        ("system", "You are a helpful assistant that extracts data from text messages and Always answer in the following json format: {json_data_format}"),
        ("human", f"Extract data from the following text message, including number or amount, currency, account type, transaction type and if receipt is required: {text_message}")
    ]
    
    '''

    dataFormat = req['format']
    text = req['text']
    template = req['template']
    message = [
        ("system", f"You are a helpful assistant that extracts data from text messages and Always answer in the following json format: {dataFormat}"),
        ("human", f"{template}: {text}")
    ]
    # Get the extracted data

    response = llm.invoke(message)
    print(response.content)
    return response.content

@app.post("/transcribe/")
async def transcribe(req: dict) -> str:
    # Load the pipeline for automatic speech recognition (ASR)
    asr_pipeline = pipeline(task="automatic-speech-recognition", model="openai/whisper-small")

    # Path to the audio file
    audio_file = "./data/cwd.wav"

    # Perform the transcription
    result = asr_pipeline(audio_file)

    # Print the transcribed text
    #print("Transcribed text:", result["text"])
    return result["text"]
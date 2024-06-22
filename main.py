import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
import aiofiles
import os
import uuid
from pathlib import Path

app = FastAPI()

# Model for the request
class TTSRequest(BaseModel):
    api_key: str
    voice: str
    model: str
    input_text: str

# Directory to save the mp3 files
TTS_DIR = "tts"
if not os.path.exists(TTS_DIR):
    os.makedirs(TTS_DIR)

@app.post("/generate_audio/")
async def generate_audio(request: TTSRequest):
    # Update the OpenAI API key for the request
    openai.api_key = request.api_key
    client = openai.OpenAI(api_key=request.api_key)

    # Generate audio using OpenAI's TTS API
    speech_file_name = f"{uuid.uuid4()}.mp3"
    speech_file_path = Path(TTS_DIR) / speech_file_name

    try:
        response = client.audio.speech.create(
            model=request.model,
            voice=request.voice,
            input=request.input_text
        )
        response.stream_to_file(speech_file_path)

        # Create the audio data URL
        audio_data_url = f"https://fastapi-render-template.onrender.com/tts/{speech_file_name}"

        # Return the HTML audio tag
        html_audio = f'<audio controls><source src="{audio_data_url}" type="audio/mp3"></audio>'
        return {"html_audio": html_audio}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tts/{file_name}")
async def serve_audio(file_name: str):
    file_path = os.path.join(TTS_DIR, file_name)
    if os.path.exists(file_path):
        return await aiofiles.open(file_path, 'rb').read()
    raise HTTPException(status_code=404, detail="File not found")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

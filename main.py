import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
import aiofiles
import os
import uuid
from pathlib import Path
from starlette.responses import StreamingResponse
import time

SWAGGER_HEADERS = {
    "title": "LINKBRICKS HORIZON-AI TTS API ENGINE",
    "version": "100.100.100",
    "description": "## 텍스트 음성 변환 엔진 \n - API Swagger \n - Multilingual TTS \n - Voice: alloy, echo, fable, onyx, nova, shimmer",
    "contact": {
        "name": "Linkbricks Horizon AI",
        "url": "https://www.linkbricks.com",
        "email": "contact@linkbricks.com",
        "license_info": {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
    },
}

app = FastAPI(**SWAGGER_HEADERS)

# 인증키
REQUIRED_AUTH_KEY = "linkbricks-saxoji-benedict-ji-01034726435!@#$%231%$#@%"

# Model for the request
class TTSRequest(BaseModel):
    api_key: str
    voice: str
    model: str
    input_text: str
    auth_key: str

# Directory to save the mp3 files
TTS_DIR = "tts"
if not os.path.exists(TTS_DIR):
    os.makedirs(TTS_DIR)

@app.post("/generate_audio/")
async def generate_audio(request: TTSRequest):
    # Check the auth key
    if request.auth_key != REQUIRED_AUTH_KEY:
        raise HTTPException(status_code=403, detail="Invalid authentication key")
    
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
        
        # Ensure the file is completely written
        while not os.path.exists(speech_file_path):
            time.sleep(0.1)
        
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
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    async def iterfile():
        async with aiofiles.open(file_path, 'rb') as f:
            while True:
                chunk = await f.read(1024)  # 파일을 1KB씩 읽기
                if not chunk:
                    break
                yield chunk

    return StreamingResponse(iterfile(), media_type="audio/mp3")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

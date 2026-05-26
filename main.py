import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
from google import genai
from dotenv import load_dotenv
import os

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI(title="YouTube Blog Generator")


class VideoRequest(BaseModel):
    url: str


def extract_video_id(url: str) -> str:
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    else:
        raise ValueError("Invalid YouTube URL")


@app.get("/")
def read_root():
    return {"message": "YouTube Blog Generator is running"}


@app.post("/generate")
def generate_blog(request: VideoRequest):
    try:
        video_id = extract_video_id(request.url)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    try:
        fetcher = YouTubeTranscriptApi()
        transcript_data = fetcher.fetch(video_id)
        transcript = " ".join([entry.text for entry in transcript_data])
    except Exception:
        raise HTTPException(status_code=404, detail="Transcript not available for this video")

    prompt = f"""
    Based on the following YouTube video transcript, write a well-structured blog post.
    Include a title, introduction, main sections, and a conclusion.
    
    Transcript:
    {transcript[:4000]}
    """

    response = client.models.generate_content(
        model="gemini-2.0-flash-lite",
        contents=prompt
    )
    return {"blog_post": response.text}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
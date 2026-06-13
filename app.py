"""RiderEx — FastAPI backend"""
import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from agents import run_riderex_pipeline
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="RiderEx")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class FeedbackRequest(BaseModel):
    feedback_text: str
    ride_id: Optional[str] = "RIDE-0000000000000001"
    vehicle_id: Optional[str] = "WM-0001"
    rating: Optional[int] = None

@app.post("/run-pipeline")
async def run_pipeline(request: FeedbackRequest):
    try:
        result = run_riderex_pipeline(
            feedback_text=request.feedback_text,
            ride_id=request.ride_id,
            vehicle_id=request.vehicle_id,
            rating=request.rating
        )
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/health")
async def health():
    band_configured = bool(os.getenv("BAND_API_KEY"))
    aiml_configured = bool(os.getenv("AIML_API_KEY"))
    return {"status": "ok", "service": "RiderEx", "agents": 5, "band_configured": band_configured, "aiml_configured": aiml_configured}

@app.get("/", response_class=HTMLResponse)
async def index():
    return open("index.html").read()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import sys

# Add parent directory to sys.path to allow importing from models
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.predict import run_prediction

app = FastAPI(title="NIDS Dashboard API", description="API for Network Intrusion Detection System Dashboard")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store latest result state
last_ml_result = None

import traceback

@app.post("/upload-data")
async def upload_data(file: UploadFile = File(...)):
    global last_ml_result

    temp_path = f"temp_{file.filename}"

    try:
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        last_ml_result = run_prediction(temp_path)

        if os.path.exists(temp_path):
            os.remove(temp_path)

    except Exception as e:
        print("ERROR OCCURRED:")
        traceback.print_exc()   # 👈 ADD THIS

        if os.path.exists(temp_path):
            os.remove(temp_path)

        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

    return JSONResponse(content=last_ml_result)

@app.get("/results")
async def get_results():
    if last_ml_result is None:
        # Return a default empty/initial state
        return JSONResponse(content={
            "summary": {"total_flows": 0, "total_anomalies": 0, "high_risk": 0},
            "table_data": [],
            "temporal_data": {"time_bucket": [], "anomaly_count": []},
            "feature_importance": []
        })
    return JSONResponse(content=last_ml_result)

# Mount frontend
app.mount("/", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static"), html=True), name="static")

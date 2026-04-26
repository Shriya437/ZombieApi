from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import sys
import uuid
import tempfile

# Add parent directory to sys.path to allow importing from models
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from models.predict import run_prediction
from auth.face_auth import build_face_database, verify_face

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

# Global variables for auth
face_db = None
VALID_TOKENS = set()

@app.on_event("startup")
def load_face_db():
    global face_db
    print("[INFO] Building face database...")
    face_db = build_face_database()

def verify_token(x_auth_token: str = Header(None)):
    if not x_auth_token or x_auth_token not in VALID_TOKENS:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return x_auth_token

@app.post("/face-login")
async def face_login(file: UploadFile = File(...)):
    global face_db
    if face_db is None:
        return JSONResponse(status_code=500, content={"success": False, "message": "Face database not initialized"})

    temp_path = None
    try:
        # Save uploaded image to temp file
        fd, temp_path = tempfile.mkstemp(suffix=".jpg")
        with os.fdopen(fd, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        # Verify face
        is_valid = verify_face(face_db, temp_path)
        
        if is_valid:
            token = str(uuid.uuid4())
            VALID_TOKENS.add(token)
            return JSONResponse(content={"success": True, "message": "Access Granted", "token": token})
        else:
            return JSONResponse(status_code=401, content={"success": False, "message": "Access Denied"})
    except Exception as e:
        print("Error in face_login:", e)
        return JSONResponse(status_code=500, content={"success": False, "message": "Server error"})
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

import traceback

@app.post("/upload-data")
async def upload_data(file: UploadFile = File(...), token: str = Depends(verify_token)):
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
async def get_results(token: str = Depends(verify_token)):
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

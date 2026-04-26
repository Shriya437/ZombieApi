from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import random
import time

app = FastAPI(title="NIDS Dashboard API", description="API for Network Intrusion Detection System Dashboard")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock state
last_mock_result = None

def generate_mock_ml_result(filename: str):
    """
    Simulates a machine learning pipeline processing a CSV file.
    Returns structured JSON with mock anomaly detection insights.
    """
    # Simulate processing time
    time.sleep(1)
    
    # In a real scenario, this would be:
    # return ml_pipeline.predict(csv_data)
    
    total_flows = random.randint(800, 1500)
    total_anomalies = int(total_flows * random.uniform(0.05, 0.15))
    high_risk = int(total_anomalies * random.uniform(0.1, 0.3))
    
    # Generate some mock table data
    table_data = []
    attack_types = ["DDoS", "Port Scan", "Botnet", "Brute Force", "Web Attack"]
    behavior_tags = ["High Traffic Burst", "Repetitive Connection", "Malicious Payload Signature", "Suspicious Geo-Location", "Rapid Authentication Failure"]
    
    for i in range(1, 11):  # Just returning top 10 for the UI
        anomaly_score = round(random.uniform(0.7, 0.99), 2)
        risk_score = round(random.uniform(0.75, 0.99), 2)
        table_data.append({
            "flow_id": random.randint(10000, 99999),
            "anomaly_score": anomaly_score,
            "is_anomaly": 1,
            "attack_type": random.choice(attack_types),
            "risk_score": risk_score,
            "risk_level": "High" if risk_score > 0.9 else "Medium",
            "behavior_tag": random.choice(behavior_tags),
            "confidence": round(random.uniform(0.8, 0.98), 2),
            "explanation": "Simulated detection of abnormal traffic pattern from file " + filename
        })
        
    return {
        "summary": {
            "total_flows": total_flows,
            "total_anomalies": total_anomalies,
            "high_risk": high_risk
        },
        "table_data": table_data,
        "temporal_data": {
            "time_bucket": ["10:00", "10:05", "10:10", "10:15", "10:20"],
            "anomaly_count": [random.randint(1, 10) for _ in range(5)]
        },
        "feature_importance": [
            {"feature": "packet_length", "importance": 0.35},
            {"feature": "flow_duration", "importance": 0.25},
            {"feature": "destination_port", "importance": 0.20},
            {"feature": "fwd_packet_length_max", "importance": 0.15},
            {"feature": "bwd_packet_length_min", "importance": 0.05}
        ]
    }

@app.post("/upload-data")
async def upload_data(file: UploadFile = File(...)):
    global last_mock_result
    
    # Normally we would save or process the CSV here
    # content = await file.read()
    
    # Generate mock result simulating ML inference
    last_mock_result = generate_mock_ml_result(file.filename)
    
    return JSONResponse(content=last_mock_result)

@app.get("/results")
async def get_results():
    if last_mock_result is None:
        # Return a default empty/initial state
        return JSONResponse(content={
            "summary": {"total_flows": 0, "total_anomalies": 0, "high_risk": 0},
            "table_data": [],
            "temporal_data": {"time_bucket": [], "anomaly_count": []},
            "feature_importance": []
        })
    return JSONResponse(content=last_mock_result)

app.mount("/", StaticFiles(directory="static", html=True), name="static")

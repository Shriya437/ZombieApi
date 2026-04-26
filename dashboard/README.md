# NIDS Dashboard - AI Security

This is the full-stack Network Intrusion Detection System (NIDS) dashboard. It features a modern, dark-themed UI and a modular FastAPI backend designed to integrate seamlessly with your upcoming Machine Learning pipeline.

## Features
- **FastAPI Backend**: Provides `POST /upload-data` and `GET /results` endpoints.
- **Frontend**: Built with Vanilla HTML, CSS, and JS (No frameworks).
- **Mock ML Pipeline**: Simulates ML predictions returning comprehensive JSON insights.
- **Modern UI**: Dark cybersecurity dashboard aesthetic with glassmorphism, pulse animations, and responsive layout.
- **ML Integration Ready**: Designed such that the ML logic can simply replace the mock data function in the backend without modifying any frontend code.

## How to Run

1. Make sure you have installed the dependencies:
   ```bash
   pip install fastapi uvicorn python-multipart
   ```

2. Start the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```

3. Open your browser and navigate to:
   ```
   http://localhost:8000/
   ```

## Using the Dashboard
1. Click **Select CSV File** and pick any `.csv` file.
2. Click **Run Analysis**.
3. Watch the dashboard dynamically populate with mock cybersecurity insights, attack patterns, feature importance, and risk metrics.

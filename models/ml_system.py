import pandas as pd
import numpy as np
import json
import warnings
import os
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.impute import SimpleImputer
import gc

warnings.filterwarnings('ignore')

def run_ml_pipeline():
    print("Loading data...")
    train_path = "ZombieApi\\data\\train_data.csv"
    test_path = "ZombieApi\\data\\test_data.csv"
    
    if not os.path.exists(train_path) or not os.path.exists(test_path):
        print(json.dumps({"error": f"Data files not found in data/ folder"}))
        return

    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)
    
    label_col = "Label"
    
    # Extract labels
    y_train = train_df[label_col].astype(str)
    X_train_raw = train_df.drop(columns=[label_col])
    X_test_raw = test_df.drop(columns=[label_col], errors='ignore')
    
    # We use all numeric columns directly as they are already preprocessed
    X_train = X_train_raw.select_dtypes(include=[np.number]).fillna(0)
    X_test = X_test_raw.select_dtypes(include=[np.number]).fillna(0)
    
    # Ensure same columns
    cols = X_train.columns.intersection(X_test.columns)
    X_train = X_train[cols]
    X_test = X_test[cols]
    features = cols.tolist()
    
    print("Training Isolation Forest...")
    # 1. Anomaly Detection (Isolation Forest)
    iso_forest = IsolationForest(contamination=0.05, random_state=42, n_jobs=-1)
    iso_forest.fit(X_train)
    
    print("Predicting anomalies...")
    anomaly_preds = iso_forest.predict(X_test)
    test_df["is_anomaly"] = np.where(anomaly_preds == -1, 1, 0)
    test_df["anomaly_score"] = iso_forest.decision_function(X_test)
    
    print("Training Random Forest...")
    # 2. Attack Classification (Random Forest)
    rf = RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1, max_depth=15)
    rf.fit(X_train, y_train)
    
    print("Predicting attacks...")
    test_df["attack_type_pred"] = rf.predict(X_test)
    probs = rf.predict_proba(X_test)
    test_df["confidence"] = probs.max(axis=1)
    
    # Free memory
    del X_train, X_test, X_train_raw, X_test_raw, train_df
    gc.collect()

    print("Computing Risk Scores...")
    # 3. Combined Intelligence System
    if "packets_per_second" not in test_df.columns:
        test_df["packets_per_second"] = 0
        
    max_packets = test_df["packets_per_second"].max()
    if pd.isna(max_packets) or max_packets == 0:
        max_packets = 1
        
    test_df["risk_score"] = (
        test_df["is_anomaly"] * 0.5 +
        (1 - test_df["confidence"]) * 0.3 +
        (test_df["packets_per_second"] / max_packets) * 0.2
    )
    
    # Normalize risk_score between 0 and 1
    r_min, r_max = test_df["risk_score"].min(), test_df["risk_score"].max()
    if r_max > r_min:
        test_df["risk_score"] = (test_df["risk_score"] - r_min) / (r_max - r_min)
    else:
        test_df["risk_score"] = np.clip(test_df["risk_score"], 0, 1)
        
    print("Assigning Risk Levels & Tags...")
    # 4. Risk Segmentation
    def assign_risk_level(score):
        if score > 0.8: return "High"
        if score > 0.5: return "Medium"
        return "Low"
        
    test_df["risk_level"] = test_df["risk_score"].apply(assign_risk_level)
    
    # 5. Behaviour Tagging
    high_pps_thresh = test_df["packets_per_second"].quantile(0.9) if len(test_df) > 0 else 0
    
    def assign_behavior(row):
        pps = row.get("packets_per_second", 0)
        syn_ratio = row.get("flag_ratio", 0)  # Provided in feature engineering
        pkt_ratio = row.get("packet_ratio", 0) # Provided in feature engineering
        
        if pps > high_pps_thresh and pps > 0:
            return "High Traffic Burst"
        elif syn_ratio > 0.5:
            return "SYN Flood Pattern"
        elif pkt_ratio > 2.0:
            return "Scanning Behavior"
        return "Normal"
            
    test_df["behavior_tag"] = test_df.apply(assign_behavior, axis=1)
    
    # 6. Explanation Engine
    def explain(row):
        exps = []
        if row["behavior_tag"] == "High Traffic Burst":
            exps.append("High packet rate indicates possible DDoS attack")
        if row["behavior_tag"] == "SYN Flood Pattern":
            exps.append("SYN imbalance indicates possible DDoS attack")
        if row["behavior_tag"] == "Scanning Behavior":
            exps.append("Irregular port scanning pattern detected")
            
        if row["is_anomaly"] == 1 and not exps:
            exps.append("Traffic pattern deviates significantly from baseline")
            
        if not exps:
            return "Traffic is within normal parameters"
        return " + ".join(exps)
        
    test_df["explanation"] = test_df.apply(explain, axis=1)
    
    # 7. Temporal Intelligence
    print("Computing Temporal Data...")
    if "Flow Duration" not in test_df.columns:
        test_df["Flow Duration"] = np.random.randint(100, 1000000, len(test_df))
        
    test_df["time_bucket"] = pd.cut(test_df["Flow Duration"], bins=10)
    time_buckets = test_df.groupby("time_bucket")["is_anomaly"].sum().reset_index()
    
    # 8. Feature Importance
    importances = rf.feature_importances_
    indices = np.argsort(importances)[::-1][:min(5, len(features))]
    top_features = [{"feature": features[i], "importance": float(importances[i])} for i in indices]
    
    print("Generating Final JSON...")
    # Limit table output to first 100 to avoid massive JSON file (since test_data is 175MB)
    output_df = test_df.head(100).copy()
    
    if "flow_id" not in output_df.columns and "Flow ID" not in output_df.columns:
        output_df["flow_id"] = range(1, len(output_df) + 1)
    elif "Flow ID" in output_df.columns:
        output_df["flow_id"] = output_df["Flow ID"]
        
    table_data = []
    for _, row in output_df.iterrows():
        table_data.append({
            "flow_id": int(row["flow_id"]) if pd.notnull(row.get("flow_id")) else 0,
            "anomaly_score": float(row["anomaly_score"]),
            "is_anomaly": int(row["is_anomaly"]),
            "attack_type": str(row["attack_type_pred"]),
            "risk_score": float(row["risk_score"]),
            "risk_level": str(row["risk_level"]),
            "behavior_tag": str(row["behavior_tag"]),
            "confidence": float(row["confidence"]),
            "explanation": str(row["explanation"])
        })
        
    output = {
        "summary": {
            "total_flows": len(test_df),
            "total_anomalies": int(test_df["is_anomaly"].sum()),
            "high_risk": int((test_df["risk_level"] == "High").sum())
        },
        "table_data": table_data,
        "temporal_data": {
            "time_bucket": [str(b) for b in time_buckets["time_bucket"]],
            "anomaly_count": [int(c) for c in time_buckets["is_anomaly"]]
        },
        "feature_importance": top_features
    }
    os.makedirs("artifacts", exist_ok=True)
    output_file = "artifacts/ml_output.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
        
    print(f"Done! Output saved to {output_file}")

if __name__ == "__main__":
    run_ml_pipeline()

def run_ml_on_uploaded_file(file_path):
    import joblib

    print("Loading uploaded data...")

    if not os.path.exists(file_path):
        return {"error": "Uploaded file not found"}

    df = pd.read_csv(file_path)

    # Load trained models
    iso = joblib.load("ZombieApi/artifacts/isolation_forest.pkl")
    rf = joblib.load("ZombieApi/artifacts/random_forest.pkl")

    label_col = "Label"

        # Load training data to get correct feature columns
    train_df = pd.read_csv("ZombieApi/data/train_data.csv")

    train_X = train_df.drop(columns=["Label"])
    train_X = train_X.select_dtypes(include=[np.number]).fillna(0)

    expected_cols = train_X.columns

    # Prepare uploaded data
    X = df.drop(columns=[label_col], errors='ignore')
    X = X.select_dtypes(include=[np.number]).fillna(0)

    # Align columns
    X = X.reindex(columns=expected_cols, fill_value=0)

    # ================= ANOMALY =================
    df["is_anomaly"] = np.where(iso.predict(X) == -1, 1, 0)
    df["anomaly_score"] = iso.decision_function(X)

    # ================= CLASSIFICATION =================
    df["attack_type_pred"] = rf.predict(X)
    df["confidence"] = rf.predict_proba(X).max(axis=1)

    # ================= RISK =================
    if "packets_per_second" not in df.columns:
        df["packets_per_second"] = 0

    max_packets = df["packets_per_second"].max() or 1

    df["risk_score"] = (
        df["is_anomaly"] * 0.5 +
        (1 - df["confidence"]) * 0.3 +
        (df["packets_per_second"] / max_packets) * 0.2
    )

    df["risk_level"] = df["risk_score"].apply(
        lambda x: "High" if x > 0.8 else "Medium" if x > 0.5 else "Low"
    )

    # ================= OUTPUT =================
    return {
        "summary": {
            "total_flows": len(df),
            "total_anomalies": int(df["is_anomaly"].sum()),
            "high_risk": int((df["risk_level"] == "High").sum())
        },
        "table_data": df.head(100).to_dict(orient="records")
    }
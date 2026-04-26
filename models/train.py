import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
import joblib

# ================= LOAD =================

train_df = pd.read_csv("ZombieApi/data/train_data.csv")

# Remove bad rows
train_df = train_df.dropna(subset=["Label"]).reset_index(drop=True)

#  Features
X_train = train_df.drop(columns=["Label"])
X_train = X_train.select_dtypes(include=[np.number]).fillna(0)

#  Labels
y_train = train_df["Label"].astype(str)

# ================= ISOLATION FOREST =================

print("\nTraining Isolation Forest...")

iso = IsolationForest(
    n_estimators=100,
    contamination=0.1,
    random_state=42,
    n_jobs=-1
)

iso.fit(X_train)

# ================= RANDOM FOREST =================

print("\nTraining Random Forest...")

rf = RandomForestClassifier(
    n_estimators=100,
    max_depth=15,
    min_samples_split=10,
    random_state=42,
    n_jobs=-1
)

rf.fit(X_train, y_train)

# ================= SAVE =================

joblib.dump(iso, "ZombieApi/artifacts/isolation_forest.pkl")
joblib.dump(rf, "ZombieApi/artifacts/random_forest.pkl")

print("\nModels trained and saved successfully!")
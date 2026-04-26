import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
import joblib

# ================= LOAD =================

train_df = pd.read_csv("data/train_data.csv")

X_train = train_df.drop(columns=["Label"])
y_train = train_df["Label"]

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

joblib.dump(iso, "artifacts/isolation_forest.pkl")
joblib.dump(rf, "artifacts/random_forest.pkl")

print("\nModels trained and saved successfully!")
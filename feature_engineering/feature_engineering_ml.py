import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib

np.random.seed(42)

# ================= LOAD =================
df = pd.read_csv("cleaned_cicids2017.csv")

# ================= LABEL ENCODING =================
labels = df["Label"]

le = LabelEncoder()
y = pd.Series(le.fit_transform(labels), index=df.index)

print("\nLabel Mapping:")
for i, label in enumerate(le.classes_):
    print(f"{label} → {i}")

print("\nClass Distribution:")
print(pd.Series(y).value_counts())

# ================= SPLIT FIRST (NO LEAKAGE) =================
X = df.drop(columns=["Label", "day", "attack_type"])

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ================= SKEW HANDLING =================

print("\nSkewness BEFORE transformation (TRAIN):")
print(X_train.skew().sort_values(ascending=False))

skewness = X_train.skew()
skewed_cols = skewness[skewness > 1].index

# ✅ FIX: avoid dtype warning
X_train = X_train.copy().astype(float)
X_test = X_test.copy().astype(float)

# Apply transformation on TRAIN
for col in skewed_cols:
    X_train.loc[:, col] = np.log1p(X_train[col].clip(lower=0))

# Apply SAME transformation on TEST
for col in skewed_cols:
    if col in X_test.columns:
        X_test.loc[:, col] = np.log1p(X_test[col].clip(lower=0))

print("\nSkewness AFTER transformation (TRAIN):")
print(X_train.skew().sort_values(ascending=False))

# ================= FEATURE IMPORTANCE (OPTIMIZED) =================

print("\nCalculating feature importance (optimized)...")

# 🔥 CRITICAL FIX: use sample instead of full data
sample_size = 100000   # reduce if laptop is slow

X_sample = X_train.sample(n=sample_size, random_state=42)
y_sample = y_train[X_sample.index]

temp_model = RandomForestClassifier(
    n_estimators=20,        # reduced trees
    random_state=42,
    n_jobs=-1               # use all CPU cores
)

temp_model.fit(X_sample, y_sample)

importances = pd.Series(temp_model.feature_importances_, index=X_train.columns)

# ================= CORRELATION ANALYSIS =================

corr_matrix = X_train.corr().abs()
upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))

drop_suggestions = set()
seen_pairs = set()

print("\nHighly Correlated Feature Pairs (>0.95):\n")

for col in upper.columns:
    high_corr = upper[col][upper[col] > 0.95]
    
    for row in high_corr.index:
        pair = tuple(sorted([row, col]))
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        
        imp_col = importances[col]
        imp_row = importances[row]
        
        if imp_col < imp_row:
            drop = col
            keep = row
        else:
            drop = row
            keep = col
        
        print(f"{row} <--> {col} | corr={upper[col][row]:.2f}")
        print(f"👉 DROP '{drop}' | KEEP '{keep}'\n")
        
        drop_suggestions.add(drop)

print("Suggested columns to drop:")
print(list(drop_suggestions))

# ================= MANUAL CONTROL =================

manual_keep = [
    "Flow Bytes/s",
    "Flow Packets/s",
    "packet_ratio",
    "iat_variability",
    "flag_ratio",
    "reset_rate"
]

manual_keep = [col for col in manual_keep if col in X_train.columns]

final_drop = [col for col in drop_suggestions if col not in manual_keep]

print("\nFinal columns after manual override:")
print(final_drop)

# ================= APPLY FEATURE SELECTION =================

X_train_reduced = X_train.drop(columns=final_drop, errors="ignore")
X_test_reduced = X_test.drop(columns=final_drop, errors="ignore")

manual_drop_extra = [
    "Flow Packets/s",
    "Flow IAT Min",
    "Fwd IAT Mean",
    "Bwd IAT Mean",
    "Total Length of Fwd Packets",
    "Total Length of Bwd Packets",
    "Total Fwd Packets",
    "Total Backward Packets",
    "endpoint_diversity",
    "reset_rate"
]

X_train_reduced = X_train_reduced.drop(columns=manual_drop_extra, errors="ignore")
X_test_reduced = X_test_reduced.drop(columns=manual_drop_extra, errors="ignore")

# ================= SCALING =================

scaler = StandardScaler()

X_train_scaled = scaler.fit_transform(X_train_reduced)
X_test_scaled = scaler.transform(X_test_reduced)

X_train_scaled = pd.DataFrame(X_train_scaled, columns=X_train_reduced.columns)
X_test_scaled = pd.DataFrame(X_test_scaled, columns=X_test_reduced.columns)

# ================= FINAL DATA =================

train_final = X_train_scaled.copy()
train_final["Label"] = y_train

test_final = X_test_scaled.copy()
test_final["Label"] = y_test

# ================= SAVE =================

train_final.to_csv("train_data.csv", index=False)
test_final.to_csv("test_data.csv", index=False)

joblib.dump(scaler, "scaler.pkl")
joblib.dump(le, "label_encoder.pkl")
joblib.dump(X_train_reduced.columns.tolist(), "feature_names.pkl")
joblib.dump(final_drop, "dropped_features.pkl")

print("\nFinal Features Used:")
print(X_train_reduced.columns.tolist())

print("\nML-ready dataset created successfully!")
print("Final feature count:", train_final.shape[1])
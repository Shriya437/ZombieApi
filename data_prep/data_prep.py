import pandas as pd
import numpy as np

files_info = [
    ("dataset\\Monday-WorkingHours.pcap_ISCX.csv","Monday", "Benign"),
    ("dataset\\Tuesday-WorkingHours.pcap_ISCX.csv","Tuesday", "Benign"),
    ("dataset\\Wednesday-WorkingHours.pcap_ISCX.csv","Wednesday", "Benign"),
    ("dataset\\Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv","Thursday", "WebAttack"),
    ("dataset\\Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv","Thursday", "Infiltration"),
    ("dataset\\Friday-WorkingHours-Morning.pcap_ISCX.csv","Friday", "Benign"),
    ("dataset\\Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv","Friday", "DDoS"),
    ("dataset\\Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv","Friday", "PortScan")
]

cleaned_dfs = []

for file, day, attack in files_info:
    print(f"Processing {file}...")
    
    df = pd.read_csv(file)
    
    #Fix column names
    df.columns = df.columns.str.strip()
    
    #Remove missing values
    df = df.dropna()
    
    #Replace infinite values
    df = df.replace([np.inf, -np.inf], 0)
    
    #Remove duplicates
    df = df.drop_duplicates()
    
    #Add metadata
    df["day"] = day
    df["attack_type"] = attack
    
    cleaned_dfs.append(df)

df = pd.concat(cleaned_dfs, ignore_index=True)

selected_columns = [
    "Destination Port",
    "Flow Duration",
    "Flow Bytes/s",
    "Flow Packets/s",
    "Total Fwd Packets",
    "Total Backward Packets",
    "Total Length of Fwd Packets",
    "Total Length of Bwd Packets",
    "Packet Length Mean",
    "Packet Length Std",
    "Average Packet Size",
    "Flow IAT Mean",
    "Flow IAT Std",
    "Flow IAT Max",
    "Flow IAT Min",
    "Fwd IAT Mean",
    "Bwd IAT Mean",
    "SYN Flag Count",
    "ACK Flag Count",
    "RST Flag Count",
    "Down/Up Ratio",
    "Label",
    "day",
    "attack_type"
]

df = df[selected_columns]

missing_cols = [col for col in selected_columns if col not in df.columns]
print("Missing Columns:", missing_cols)

#creating derived features
df["Down/Up Ratio"] = df["Down/Up Ratio"].replace([np.inf, -np.inf], 0)

df["total_packets"] = df["Total Fwd Packets"] + df["Total Backward Packets"]

df["total_bytes"] = df["Total Length of Fwd Packets"] + df["Total Length of Bwd Packets"]

df["bytes_per_packet"] = df["total_bytes"] / (df["total_packets"] + 1)

df["packet_ratio"] = df["Total Fwd Packets"] / (df["Total Backward Packets"] + 1)

# Remove invalid durations
df = df[df["Flow Duration"] > 0]

# Clip extreme outliers
df["Flow Duration"] = df["Flow Duration"].clip(upper=df["Flow Duration"].quantile(0.99))
df["packet_ratio"] = df["packet_ratio"].clip(upper=df["packet_ratio"].quantile(0.99))
df["Down/Up Ratio"] = df["Down/Up Ratio"].clip(upper=df["Down/Up Ratio"].quantile(0.99))

df["Label"] = df["Label"].str.strip()
# 🔹 Fix weird dash issue
df["Label"] = df["Label"].str.replace("�", "-", regex=False)
df["Label"] = df["Label"].replace({
    # Normal
    "BENIGN": "Benign",
    
    # DDoS group
    "DoS Hulk": "DDoS",
    "DoS GoldenEye": "DDoS",
    "DoS slowloris": "DDoS",
    "DoS Slowhttptest": "DDoS",
    
    # Port scan
    "PortScan": "PortScan",
    
    # Web attacks (now will match correctly)
    "Web Attack - Brute Force": "WebAttack",
    "Web Attack - XSS": "WebAttack",
    "Web Attack - Sql Injection": "WebAttack",
    
    # Other attacks (group them)
    "FTP-Patator": "BruteForce",
    "SSH-Patator": "BruteForce",
    
    "Bot": "Bot",
    "Heartbleed": "Heartbleed",
    
    "Infiltration": "Infiltration"
})
df["Label"] = df["Label"].replace({
    "BruteForce": "Attack",
    "Bot": "Attack",
    "Heartbleed": "Attack",
    "Infiltration": "Attack"
})
print(df["Label"].value_counts())

print(df.isnull().sum())
print(df.describe())

#Save to databasse
from sqlalchemy import create_engine

# Create database
engine = create_engine("sqlite:///aether.db")

# Save dataframe
df.to_sql("raw_data", engine, if_exists="replace", index=False)

print("Data saved successfully!")

def fetch_raw_data():
    return pd.read_sql("SELECT * FROM raw_data", engine)

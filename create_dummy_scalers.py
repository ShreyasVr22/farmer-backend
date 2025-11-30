"""
Create dummy scalers for all 21 hobli locations
This allows the API to start while training is happening
"""

import joblib
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler
import numpy as np

LOCATIONS = [
    "kasaba_doddaballapura", "doddabelavangala_doddaballapura", "thubagere_doddaballapura",
    "sasalu_doddaballapura", "madhure_doddaballapura",
    "kasaba_devanahalli", "vijayapura_devanahalli", "kundana_devanahalli",
    "bettakote_devanahalli", "undire_devanahalli",
    "sulibele_hosakote", "anugondanahalli_hosakote", "jadigenahalli_hosakote",
    "nandagudi_hosakote", "kasaba_hosakote",
    "kasaba_nelamangala", "huliyurdurga_nelamangala", "tyamagondlu_nelamangala",
    "sompura_nelamangala", "lakshmipura_nelamangala", "makali_nelamangala"
]

def create_dummy_scaler():
    """Create a dummy scaler with typical weather value ranges"""
    scaler = MinMaxScaler()
    # Fit with typical temp/rainfall ranges for Bangalore
    # temp_max: 20-45C, temp_min: 10-35C, rainfall: 0-100mm
    sample_data = np.array([
        [20, 10, 0],    # min values
        [45, 35, 100],  # max values
    ])
    scaler.fit(sample_data)
    return scaler

scaler_dir = Path("models/locations")
scaler_dir.mkdir(parents=True, exist_ok=True)

print(f"Creating {len(LOCATIONS)} dummy scalers...")
for location in LOCATIONS:
    scaler = create_dummy_scaler()
    scaler_path = scaler_dir / f"scaler_{location}.pkl"
    joblib.dump(scaler, str(scaler_path))
    print(f"[OK] {location}")

print(f"\nCreated {len(LOCATIONS)} scalers in models/locations/")

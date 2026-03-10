from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH_NAMES = BASE_DIR / "data" / "names.json"
DATA_PATH_ENCOUNTERS = BASE_DIR / "data" / "encounters.json"

with open(DATA_PATH_NAMES) as f:
    NAMES = json.load(f)

with open(DATA_PATH_ENCOUNTERS) as f:
    ENCOUNTERS = json.load(f)
import os

# Path configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "svd_model.pkl")
METADATA_PATH = os.path.join(BASE_DIR, "data", "myanilist.csv")
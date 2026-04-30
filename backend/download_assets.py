import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ID = os.environ.get("HF_REPO_ID", "DawitBonga/myanilist-recommender")
HF_TOKEN = os.environ.get("HF_TOKEN")

ASSETS = [
    ("svd_model.pkl", os.path.join(BASE_DIR, "models")),
    ("myanilist.csv", os.path.join(BASE_DIR, "data")),
]


def download_asset(filename, local_dir):
    target_path = os.path.join(local_dir, filename)
    if os.path.exists(target_path):
        print(f"{target_path} already exists")
        return target_path

    from huggingface_hub import hf_hub_download

    os.makedirs(local_dir, exist_ok=True)
    print(f"Downloading {filename} from Hugging Face repo {REPO_ID}...")
    return hf_hub_download(
        repo_id=REPO_ID,
        filename=filename,
        local_dir=local_dir,
        token=HF_TOKEN,
    )


def main():
    for filename, local_dir in ASSETS:
        download_asset(filename, local_dir)

    print("Assets ready.")


if __name__ == "__main__":
    main()

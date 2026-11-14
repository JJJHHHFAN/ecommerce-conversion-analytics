"""Fetch original RetailRocket CSVs from the public Hugging Face mirror."""

import hashlib
import shutil
from pathlib import Path

from huggingface_hub import hf_hub_download

ROOT = Path(__file__).resolve().parents[1]
REPO = "DanielKiani/RetailRocket-Recommender-Data"
PREFIX = "data/RetailRocket-Recommender-Data/data/"


def main():
    raw_dir = ROOT / "data/raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    for name in ["events.csv", "category_tree.csv"]:
        src = Path(hf_hub_download(repo_id=REPO, repo_type="dataset", filename=PREFIX + name))
        dst = raw_dir / name
        shutil.copy2(src, dst)
        h = hashlib.sha256(dst.read_bytes()).hexdigest()
        print(f"{name}: {dst.stat().st_size:,} bytes, SHA-256 {h}")


if __name__ == "__main__":
    main()

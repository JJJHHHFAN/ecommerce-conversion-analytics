"""Fetch original RetailRocket CSVs from the public Hugging Face mirror."""

import hashlib
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = "DanielKiani/RetailRocket-Recommender-Data"
PREFIX = "data/RetailRocket-Recommender-Data/data/"
EXPECTED_SHA256 = {
    "events.csv": "3745aa83238b1e6d44d8fda209807899f420084398f94ddf745f3cbcfecbf9e7",
    "category_tree.csv": "94e865eb0a3d48cbbfe3b79079018dd92509315c88f5fd8d00d0b4b5af434f5b",
}


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    raw_dir = ROOT / "data/raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    for name in ["events.csv", "category_tree.csv"]:
        dst = raw_dir / name
        if dst.exists() and sha256(dst) == EXPECTED_SHA256[name]:
            print(f"{name}: verified existing file, SHA-256 {EXPECTED_SHA256[name]}")
            continue
        from huggingface_hub import hf_hub_download
        src = Path(hf_hub_download(repo_id=REPO, repo_type="dataset", filename=PREFIX + name))
        actual = sha256(src)
        if actual != EXPECTED_SHA256[name]:
            raise ValueError(f"Unexpected SHA-256 for {name}: {actual}")
        shutil.copy2(src, dst)
        print(f"{name}: {dst.stat().st_size:,} bytes, SHA-256 {actual}")


if __name__ == "__main__":
    main()

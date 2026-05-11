"""
images.py — Download and filter Kaggle invoice images
=====================================================
Downloads the Kaggle dataset and selects batch1-0331 to batch1-0381 (50 images).

Usage:
    python images.py
    python images.py --output-dir ./my_images
"""

import os
import re
import shutil
import argparse
from pathlib import Path


def download_and_select(output_dir: str = None):
    """Download dataset from Kaggle and copy selected images to output_dir."""
    try:
        import kagglehub
    except ImportError:
        raise ImportError("kagglehub not installed. Run: pip install kagglehub")

    if output_dir is None:
        output_dir = str(Path(__file__).parent / "selected_images")

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    print("Downloading Kaggle dataset...")
    dataset_path = kagglehub.dataset_download(
        "osamahosamabdellatif/high-quality-invoice-images-for-ocr"
    )
    print(f"   Dataset downloaded to: {dataset_path}")

    # Walk and find all images matching batch1-0331 to batch1-0381
    selected = []
    for root, _, files in os.walk(dataset_path):
        for fname in files:
            if fname.lower().endswith((".jpg", ".jpeg", ".png")):
                match = re.search(r"batch1[-_](\d+)", fname, re.IGNORECASE)
                if match and 331 <= int(match.group(1)) <= 381:
                    selected.append(os.path.join(root, fname))

    selected = sorted(selected)
    print(f"   Found {len(selected)} matching images (batch1-0331 → batch1-0381)")

    for src in selected:
        dst = os.path.join(output_dir, Path(src).name)
        shutil.copy2(src, dst)

    print(f"{len(selected)} images copied to: {output_dir}")
    return output_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download Kaggle invoice images")
    parser.add_argument(
        "--output-dir", "-o",
        default=str(Path(__file__).parent / "selected_images"),
        help="Directory to save selected images (default: ./selected_images)",
    )
    args = parser.parse_args()
    download_and_select(args.output_dir)

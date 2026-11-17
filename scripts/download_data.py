"""Re-download the raw data into data/raw/ (raw data is not committed to git).

Usage (from the repository root):
    python scripts/download_data.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.fetch import download_all  # noqa: E402

if __name__ == "__main__":
    stations, measurements = download_all()
    print(f"Saved {stations}\nSaved {measurements}")

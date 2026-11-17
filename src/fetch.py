"""Download air quality data from the Regione Lombardia Socrata API.

The API is public and needs no key. We page through results with ``$limit`` /
``$offset`` and a stable ``$order`` so that no rows are skipped or duplicated.
"""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import requests

from .config import DATA_RAW, MEASUREMENT_DATASETS, SENSORS, SOCRATA_BASE, STATIONS_DATASET

PAGE_SIZE = 50_000


def _get(url: str, params: dict, retries: int = 4, timeout: int = 300) -> list[dict]:
    """GET a Socrata endpoint and return the decoded JSON rows, retrying on network errors."""
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** (attempt + 1))
    return []  # unreachable


def fetch_paged(dataset_id: str, where: str, select: str | None = None, order: str = ":id") -> pd.DataFrame:
    """Fetch every row of a Socrata dataset matching a SoQL ``where`` clause.

    Args:
        dataset_id: Socrata 4x4 dataset identifier, e.g. ``"g2hp-ar79"``.
        where: SoQL filter, e.g. ``"idsensore in('5531')"``.
        select: optional SoQL column list.
        order: column(s) to sort by; needed for stable paging.

    Returns:
        A DataFrame with all matching rows (all columns as strings, as returned by the API).
    """
    url = f"{SOCRATA_BASE}/{dataset_id}.json"
    rows: list[dict] = []
    offset = 0
    while True:
        params = {"$where": where, "$limit": PAGE_SIZE, "$offset": offset, "$order": order}
        if select:
            params["$select"] = select
        page = _get(url, params)
        rows.extend(page)
        if len(page) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return pd.DataFrame(rows)


def fetch_stations() -> pd.DataFrame:
    """Download sensor/station metadata for all Milan sensors (dataset ``ib47-atvt``)."""
    cols = "idsensore,nometiposensore,unitamisura,idstazione,nomestazione,quota,comune,storico,datastart,datastop,lat,lng"
    return fetch_paged(STATIONS_DATASET, where="comune='Milano'", select=cols, order="idsensore")


def fetch_measurements(sensor_ids: list[str] | None = None) -> pd.DataFrame:
    """Download raw measurements for the chosen sensors across all archive datasets.

    Each archive dataset is queried only for its own half-open date window
    (see ``config.MEASUREMENT_DATASETS``) so the result has no overlaps.

    Returns:
        DataFrame with columns ``idsensore, data, valore, stato, idoperatore, dataset``.
    """
    sensor_ids = sensor_ids or list(SENSORS)
    id_list = ",".join(f"'{s}'" for s in sensor_ids)
    frames = []
    for dataset_id, (start, end) in MEASUREMENT_DATASETS.items():
        where = f"idsensore in({id_list}) AND data >= '{start}' AND data < '{end}'"
        df = fetch_paged(dataset_id, where=where, order="idsensore,data")
        df["dataset"] = dataset_id
        print(f"{dataset_id}: {len(df):,} rows")
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def load_raw(path: Path = DATA_RAW / "measurements_milano.csv") -> pd.DataFrame:
    """Read the raw measurements CSV safely.

    Pitfall: by default pandas reads the text ``"NA"`` as a missing value. In this
    data ``"NA"`` is a real flag value ("not valid"), so we disable that behaviour and
    keep the ``stato`` column exactly as ARPA published it.
    """
    return pd.read_csv(path, dtype={"idsensore": str, "stato": str}, keep_default_na=False, na_values={"valore": [""]})


def download_all(out_dir: Path = DATA_RAW) -> tuple[Path, Path]:
    """Download stations and measurements and save them as raw CSV files.

    Returns:
        Paths of the stations file and the measurements file.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    stations_path = out_dir / "stations_milano.csv"
    meas_path = out_dir / "measurements_milano.csv"
    fetch_stations().to_csv(stations_path, index=False)
    fetch_measurements().to_csv(meas_path, index=False)
    return stations_path, meas_path

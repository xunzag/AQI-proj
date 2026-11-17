"""Project-wide constants: dataset IDs, the Milan sensors we use, and WHO guideline values.

Keeping these in one place means every notebook uses exactly the same stations,
thresholds and labels, so results are consistent and easy to audit.
"""

from pathlib import Path

# --- Paths -------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "figures"

# --- Regione Lombardia open data portal (Socrata) ----------------------------
SOCRATA_BASE = "https://www.dati.lombardia.it/resource"

STATIONS_DATASET = "ib47-atvt"  # station & sensor metadata ("Stazioni qualità dell'aria")

# ARPA Lombardia splits measurements into archive datasets by period.
# Each entry: dataset id -> (first date we take, first date we do NOT take).
# Ranges are half-open and non-overlapping, so no timestamp is downloaded twice.
MEASUREMENT_DATASETS = {
    "nr8w-tj77": ("2015-01-01T00:00:00", "2018-01-01T00:00:00"),  # "Dati sensori aria 2010-2017"
    "g2hp-ar79": ("2018-01-01T00:00:00", "2026-01-01T00:00:00"),  # "Dati sensori aria dal 2018"
    "nicp-bhqi": ("2026-01-01T00:00:00", "2100-01-01T00:00:00"),  # "Dati sensori aria" (current year)
}

# --- Milan sensors -------------------------------------------------------------
# idsensore -> (pollutant, station name). Chosen in Step 0: stations that are active
# over the whole 2015-today period, so the city average is not distorted by
# stations opening or closing mid-way.
SENSORS = {
    # PM10 (daily values, gravimetric/equivalent method "SM2005")
    "6956": ("PM10", "Milano Verziere"),
    "10320": ("PM10", "Milano v.Senato"),
    "10273": ("PM10", "Milano Pascal Città Studi"),
    # PM2.5 (daily values)
    "17122": ("PM2.5", "Milano v.Senato"),
    "10283": ("PM2.5", "Milano Pascal Città Studi"),
    # NO2 (hourly values)
    "5531": ("NO2", "Milano Verziere"),
    "5551": ("NO2", "Milano v.Senato"),
    "10279": ("NO2", "Milano Pascal Città Studi"),
    "5504": ("NO2", "Milano v.Marche"),
    "5542": ("NO2", "Milano v.Liguria"),
}

POLLUTANTS = ["PM10", "PM2.5", "NO2"]

# --- WHO Global Air Quality Guidelines (2021), µg/m³ ---------------------------
# Source: WHO global air quality guidelines, 2021, Executive summary, Table 0.1.
# The 24-hour guideline is defined as the 99th percentile of daily values
# (i.e. it should be exceeded on no more than 3-4 days per year).
WHO_ANNUAL = {"PM10": 15, "PM2.5": 5, "NO2": 10}
WHO_DAILY = {"PM10": 45, "PM2.5": 15, "NO2": 25}

# EU limit values (Directive 2008/50/EC) for context: PM10 daily 50 µg/m³ not to be
# exceeded more than 35 days/year; annual means PM10 40, PM2.5 25, NO2 40 µg/m³.
EU_PM10_DAILY_LIMIT = 50
EU_PM10_MAX_EXCEEDANCE_DAYS = 35

UNIT = "µg/m³"
SOURCE_NOTE = "Source: ARPA Lombardia / Regione Lombardia open data (dati.lombardia.it)"

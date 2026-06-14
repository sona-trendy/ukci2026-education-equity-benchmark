# =============================================================
# utils.py
#
# Provides
# --------
# - Config loaders (indicators.yml, pipeline.yml)
# - Repository root discovery
# - World Bank WDI + WGI API fetch logic (with ISO2 supplement fix)
# - UNESCO UIS fetch logic — two modes:
#     API mode  : REST calls to api.uis.unesco.org (key required)
#     BDDS mode : bulk CSV download, local cache, no key needed
# - Shared deduplication, income sort, coverage helpers
# =============================================================

from __future__ import annotations

import io
import math
import os
import time
import zipfile
from pathlib import Path

import pandas as pd
import requests


# ──────────────────────────────────────────────────────────────
# Repository root discovery
# ──────────────────────────────────────────────────────────────
def find_project_root(start: Path | None = None) -> Path:
    if start is None:
        try:
            start = Path(__file__).resolve()
        except NameError:
            start = Path.cwd().resolve()
    start = Path(start).resolve()
    if start.is_file():
        start = start.parent
    markers = [".git", "pyproject.toml", "requirements.txt",
                "environment.yml", "README.md"]
    for candidate in [start, *start.parents]:
        if any((candidate / m).exists() for m in markers):
            return candidate
    return start.parent if start.name.lower() == "src" else start


# ──────────────────────────────────────────────────────────────
# Config loaders
# ──────────────────────────────────────────────────────────────
def _yaml():
    try:
        import yaml
        return yaml
    except ImportError:
        raise ImportError("PyYAML required: pip install pyyaml")


def load_indicators(config_path: Path | None = None) -> dict:
    """Load indicators.yml → raw dict."""
    if config_path is None:
        config_path = find_project_root() / "configs" / "indicators.yml"
    with open(config_path, encoding="utf-8") as fh:
        return _yaml().safe_load(fh)


def load_pipeline(config_path: Path | None = None) -> dict:
    """Load pipeline.yml → raw dict."""
    if config_path is None:
        config_path = find_project_root() / "configs" / "pipeline.yml"
    with open(config_path, encoding="utf-8") as fh:
        return _yaml().safe_load(fh)


# ── Indicator maps derived from indicators.yml ────────────────
def by_source(ind_cfg: dict, source: str) -> dict[str, dict]:
    """Return {nice_name: spec} for all indicators with a given source."""
    return {k: v for k, v in ind_cfg["indicators"].items()
            if v.get("source") == source}


def clip_map(ind_cfg: dict) -> dict[str, tuple[float, float]]:
    """Return {nice_name: (lo, hi)} for all clipped indicators."""
    out = {}
    for name, spec in ind_cfg["indicators"].items():
        lo = spec.get("clip_min")
        hi = spec.get("clip_max")
        if lo is not None or hi is not None:
            lo_f = float("-inf") if lo is None else (math.inf if lo == float("inf") else float(lo))
            hi_f = float("inf")  if hi is None else (math.inf if hi == float("inf") else float(hi))
            out[name] = (lo_f, hi_f)
    return out


# ──────────────────────────────────────────────────────────────
# Income group sort order
# ──────────────────────────────────────────────────────────────
INCOME_ORDER: dict[str, int] = {
    "High income":         0,
    "Upper middle income": 1,
    "Lower middle income": 2,
    "Low income":          3,
    "Unknown":             4,
}


def sort_by_income(
    df: pd.DataFrame,
    extra_cols: list[str] | None = None,
    ascending: list[bool] | None = None,
) -> pd.DataFrame:
    df = df.copy()
    df["_isort"] = df["income_group"].map(INCOME_ORDER).fillna(4).astype(int)
    cols = ["_isort"] + (extra_cols or [])
    asc  = [True]     + (ascending  or [True] * len(extra_cols or []))
    return df.sort_values(cols, ascending=asc).drop(columns="_isort").reset_index(drop=True)


# ──────────────────────────────────────────────────────────────
# HTTP helpers (shared by WB and UIS API modes)
# ──────────────────────────────────────────────────────────────
def _retry_get(
    url: str,
    params: dict | None = None,
    headers: dict | None = None,
    allow_400: bool = False,
    max_retries: int = 4,
    sleep: float = 0.25,
    timeout: int = 60,
) -> requests.Response:
    """
    GET with exponential backoff.

    Retries on:
      - HTTP 429, 500, 502, 503, 504
      - requests.Timeout  (connect or read timeout — e.g. slow WB API)
      - requests.ConnectionError  (dropped connection, DNS hiccup)

    Returns 400 responses to the caller without raising when allow_400=True.
    Raises RuntimeError after max_retries exhausted.
    """
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=timeout)

            if allow_400 and resp.status_code == 400:
                return resp

            if resp.status_code in (429, 500, 502, 503, 504):
                # 502 from WB Azure gateway needs a longer pause —
                # short retries just hit the same overloaded window.
                # Back-off: 5s, 15s, 30s, 60s, 90s, 120s
                wait = min(5 * (3 ** (attempt - 1)), 120)
                time.sleep(wait)
                continue

            resp.raise_for_status()
            return resp

        except (requests.Timeout, requests.ConnectionError) as exc:
            # Transient network issue — always retry with longer back-off
            if attempt == max_retries:
                raise RuntimeError(
                    f"Exceeded {max_retries} retries (timeout/connection) for {url}"
                ) from exc
            wait = sleep * attempt * 3
            time.sleep(wait)

        except requests.RequestException:
            if attempt == max_retries:
                raise
            time.sleep(sleep * attempt * 2)

    raise RuntimeError(f"Exceeded {max_retries} retries for {url}")


def _chunked(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i: i + size]


# ──────────────────────────────────────────────────────────────
# World Bank helpers (WDI + WGI)
# ──────────────────────────────────────────────────────────────
def wb_get_countries(wb_cfg: dict) -> pd.DataFrame:
    """
    Fetch all non-aggregate World Bank economies with income groups.
    Aggregates are excluded via region.id == 'NA'.
    """
    url    = f"{wb_cfg['base']}/country"
    params = {"format": "json", "per_page": 400, "page": 1}
    resp   = _retry_get(url, params, max_retries=wb_cfg["max_retries"],
                        sleep=wb_cfg["sleep"], timeout=wb_cfg["timeout"])
    data   = resp.json()
    if not isinstance(data, list) or len(data) < 2:
        raise RuntimeError("Unexpected World Bank country API response.")
    pages = int(data[0].get("pages", 1))
    rows  = list(data[1])
    for page in range(2, pages + 1):
        time.sleep(wb_cfg["sleep"])
        r = _retry_get(url, {**params, "page": page},
                       max_retries=wb_cfg["max_retries"],
                       sleep=wb_cfg["sleep"], timeout=wb_cfg["timeout"])
        d = r.json()
        if isinstance(d, list) and len(d) > 1:
            rows.extend(d[1])
    records = []
    for row in rows:
        if (row.get("region") or {}).get("id") == "NA":
            continue
        iso3c = row.get("id")
        iso2c = row.get("iso2Code")
        name  = row.get("name")
        inc   = (row.get("incomeLevel") or {}).get("value")
        if iso3c and name:
            records.append({
                "iso3c":        str(iso3c).upper(),
                "iso2c":        str(iso2c).upper() if iso2c else None,
                "country":      name,
                "income_group": inc or "Unknown",
            })
    df = pd.DataFrame(records).drop_duplicates("iso3c")
    if df.empty:
        raise RuntimeError("No non-aggregate countries returned.")
    return df


def build_iso2_map(countries_df: pd.DataFrame, supplement: dict) -> dict[str, str]:
    """Build ISO2 → ISO3 lookup with WGI-gap supplement."""
    base = (countries_df.dropna(subset=["iso2c"])
            .assign(iso2c=lambda d: d["iso2c"].str.upper())
            .set_index("iso2c")["iso3c"].to_dict())
    base.update({k.upper(): v.upper() for k, v in supplement.items()})
    return base


def _normalise_iso3(row: dict, iso2_map: dict) -> str | None:
    iso3 = row.get("countryiso3code")
    if iso3:
        iso3 = str(iso3).strip().upper()
        if iso3:
            return iso3
    cid = (row.get("country") or {}).get("id")
    if not cid:
        return None
    cid = str(cid).strip().upper()
    if len(cid) == 3:
        return cid
    if len(cid) == 2:
        return iso2_map.get(cid)
    return None


def _parse_wb_rows(
    rows: list[dict],
    nice: str,
    year_min: int,
    year_max: int,
    iso_set: set[str],
    iso2_map: dict,
) -> list[dict]:
    out = []
    for row in rows:
        iso3 = _normalise_iso3(row, iso2_map)
        if not iso3 or iso3 not in iso_set:
            continue
        country = (row.get("country") or {}).get("value")
        date    = row.get("date")
        value   = row.get("value")
        if not country or not date:
            continue
        try:
            year = int(date)
        except (TypeError, ValueError):
            continue
        if year_min <= year <= year_max:
            out.append({"iso3c": iso3, "country": country,
                        "nice": nice, "year": year, "value": value})
    return out


def wb_fetch_indicator(
    iso_list:  list[str],
    nice:      str,
    wb_code:   str,
    year_min:  int,
    year_max:  int,
    iso2_map:  dict,
    wb_cfg:    dict,
    source:    str | None = None,
) -> pd.DataFrame:
    """
    Fetch one WDI/WGI indicator for a list of countries.
    Recursively bisects batches that return HTTP 400 (WGI source=75 behaviour).
    """
    iso_set   = {str(c).upper() for c in iso_list}
    out_rows: list[dict] = []
    skipped:  list[str]  = []

    def push(rows):
        out_rows.extend(_parse_wb_rows(rows, nice, year_min, year_max, iso_set, iso2_map))

    def _api_params(page=1):
        p = {"date": f"{year_min}:{year_max}", "format": "json",
             "per_page": wb_cfg["per_page"], "page": page}
        if source:
            p["source"] = str(source)
        return p

    def fetch_chunk(chunk):
        url = f"{wb_cfg['base']}/country/{';'.join(chunk)}/indicator/{wb_code}"
        try:
            resp = _retry_get(url, _api_params(), allow_400=True,
                              max_retries=wb_cfg["max_retries"],
                              sleep=wb_cfg["sleep"], timeout=wb_cfg["timeout"])
        except requests.RequestException:
            if len(chunk) == 1:
                skipped.append(chunk[0]); return
            mid = len(chunk) // 2
            time.sleep(wb_cfg["sleep"])
            fetch_chunk(chunk[:mid]); fetch_chunk(chunk[mid:])
            return

        if resp.status_code == 400:
            if len(chunk) == 1:
                skipped.append(chunk[0]); return
            mid = len(chunk) // 2
            time.sleep(wb_cfg["sleep"])
            fetch_chunk(chunk[:mid]); fetch_chunk(chunk[mid:])
            return

        data = resp.json()
        if not isinstance(data, list) or len(data) < 2 or not isinstance(data[1], list):
            return
        meta, rows = data[0], data[1]
        pages = int(meta.get("pages", 1))
        push(rows)
        for page in range(2, pages + 1):
            time.sleep(wb_cfg["sleep"])
            try:
                pr = _retry_get(url, _api_params(page), allow_400=True,
                                max_retries=wb_cfg["max_retries"],
                                sleep=wb_cfg["sleep"], timeout=wb_cfg["timeout"])
                if pr.status_code == 400:
                    break
                pd_ = pr.json()
                if isinstance(pd_, list) and len(pd_) > 1 and isinstance(pd_[1], list):
                    push(pd_[1])
            except requests.RequestException:
                break

    for chunk in _chunked(iso_list, wb_cfg["batch_size"]):
        fetch_chunk(chunk)
        time.sleep(wb_cfg["sleep"])

    if skipped:
        print(f"  [warn] {nice}: skipped {len(skipped)} ISO(s) — "
              f"{', '.join(skipped[:8])}{'…' if len(skipped) > 8 else ''}")

    if not out_rows:
        return pd.DataFrame(columns=["iso3c", "country", "nice", "year", "value"])
    return pd.DataFrame(out_rows)


# ──────────────────────────────────────────────────────────────
# UNESCO UIS — API mode
# ──────────────────────────────────────────────────────────────
def uis_api_fetch(
    iso_list:  list[str],
    nice:      str,
    uis_code:  str,
    year_min:  int,
    year_max:  int,
    uis_cfg:   dict,
    api_key:   str,
) -> pd.DataFrame:
    """
    Fetch one UIS indicator via the REST API.
    Endpoint: GET /api/public/data
    Auth:     Ocp-Apim-Subscription-Key header (or query param)
    Batches countries in groups of 50 (100k record limit per call).

    Response structure:
      { "data": [ { "geoUnit": "ESP", "year": 2020, "value": 98.5,
                    "indicatorId": "TRTP", ... }, ... ] }
    """
    base    = uis_cfg["api_base"].rstrip("/")
    headers = {
        "Ocp-Apim-Subscription-Key": api_key,
        "Accept": "application/json",
    }
    timeout = uis_cfg.get("timeout", 60)
    retries = uis_cfg.get("max_retries", 4)

    out_rows: list[dict] = []

    # UIS API accepts comma-separated geoUnits; batch to stay under 100k limit
    for chunk in _chunked(iso_list, 50):
        params = {
            "indicator":  uis_code,
            "geoUnit":    ",".join(chunk),
            "startYear":  year_min,
            "endYear":    year_max,
            "geoUnitType": "NATIONAL",
        }
        url = f"{base}/api/public/data"

        try:
            resp = _retry_get(url, params=params, headers=headers,
                              max_retries=retries, timeout=timeout)
        except requests.RequestException as exc:
            print(f"  [warn] UIS API error for {nice}: {exc}")
            continue

        try:
            payload = resp.json()
        except Exception:
            print(f"  [warn] UIS API non-JSON response for {nice}")
            continue

        records = payload if isinstance(payload, list) else payload.get("data", [])

        for rec in records:
            iso3   = str(rec.get("geoUnit") or rec.get("countryId") or "").upper()
            year   = rec.get("year") or rec.get("period")
            value  = rec.get("value")
            cname  = rec.get("geoUnitName") or iso3
            if iso3 and year:
                try:
                    year = int(year)
                except (TypeError, ValueError):
                    continue
                if year_min <= year <= year_max:
                    out_rows.append({
                        "iso3c":   iso3,
                        "country": cname,
                        "nice":    nice,
                        "year":    year,
                        "value":   value,
                    })
        time.sleep(0.2)

    if not out_rows:
        return pd.DataFrame(columns=["iso3c", "country", "nice", "year", "value"])
    return pd.DataFrame(out_rows)


# ──────────────────────────────────────────────────────────────
# UNESCO UIS — BDDS (bulk download) mode
# ──────────────────────────────────────────────────────────────
_BDDS_CACHE: dict[str, pd.DataFrame] = {}   # in-process cache


def _download_bdds_zip(url: str, cache_dir: Path, timeout: int) -> Path:
    """
    Download a BDDS zip to cache_dir if not already present.
    Returns the local path.

    URL pattern (February 2026 release):
      https://download.uis.unesco.org/bdds/202602/SDG.zip
      https://download.uis.unesco.org/bdds/202602/OPRI.zip
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    fname = url.rstrip("/").split("/")[-1]   # e.g. "SDG.zip"
    local = cache_dir / fname
    if local.exists():
        print(f"  [cache] Using cached BDDS file: {local.name}")
        return local
    print(f"  [download] Fetching {url}  …")
    resp = requests.get(url, stream=True, timeout=timeout)
    resp.raise_for_status()
    bytes_written = 0
    with open(local, "wb") as fh:
        for chunk in resp.iter_content(chunk_size=1 << 20):   # 1 MB chunks
            fh.write(chunk)
            bytes_written += len(chunk)
    print(f"  [download] Saved {local.name}  ({bytes_written / 1e6:.1f} MB)")
    return local


def _read_bdds_zip(local_path: Path, expected_csv: str | None = None) -> pd.DataFrame:
    """
    Read the national-level data CSV from a BDDS zip archive.

    February 2026 zip layout (confirmed):
      SDG.zip   contains: SDG_COUNTRY.csv, SDG_DATA_NATIONAL.csv (75 MB),
                           SDG_DATA_REGIONAL.csv, SDG_LABEL.csv,
                           SDG_METADATA.csv, SDG_README_*.md, SDG_REGION.csv
      OPRI.zip  contains: OPRI_COUNTRY.csv, OPRI_DATA_NATIONAL.csv (173 MB), …

    IMPORTANT: Must select DATA_NATIONAL explicitly — taking the first .csv
    alphabetically gives COUNTRY.csv which has only 2 columns.

    OPRI INDICATOR_ID values are integers stored as strings after normalisation.
    SDG  INDICATOR_ID values are dot-notation strings (e.g. 'TRTP.1').
    """
    cache_key = str(local_path)
    if cache_key in _BDDS_CACHE:
        return _BDDS_CACHE[cache_key]

    print(f"  [parse] Reading {local_path.name} …")

    with zipfile.ZipFile(local_path) as zf:
        names = zf.namelist()

        # Priority 1: explicitly expected CSV name
        target = None
        if expected_csv and expected_csv in names:
            target = expected_csv
        else:
            # Priority 2: file whose name contains DATA_NATIONAL (not REGIONAL)
            candidates = [
                n for n in names
                if "DATA_NATIONAL" in n.upper()
                and "REGIONAL" not in n.upper()
                and n.upper().endswith(".CSV")
            ]
            if candidates:
                target = candidates[0]

        if target is None:
            raise RuntimeError(
                f"No DATA_NATIONAL CSV found in {local_path.name}. "
                f"Contents: {names}"
            )

        print(f"  [parse]   Reading {target}")
        with zf.open(target) as cf:
            df = pd.read_csv(cf, low_memory=False)

    df.columns = [c.strip().upper() for c in df.columns]
    # Normalise INDICATOR_ID to string (OPRI uses integers)
    if "INDICATOR_ID" in df.columns:
        df["INDICATOR_ID"] = df["INDICATOR_ID"].astype(str).str.strip().str.upper()
    _BDDS_CACHE[cache_key] = df
    print(f"  [parse]   Rows loaded: {len(df):,}  columns: {list(df.columns[:8])}")
    return df


def _resolve_bdds_columns(df: pd.DataFrame) -> tuple[str, str, str, str] | None:
    """
    Detect column names for INDICATOR_ID, COUNTRY_ID, YEAR, VALUE
    across BDDS release variants.

    Known layouts:
      Feb 2026: INDICATOR_ID, COUNTRY_ID, YEAR, VALUE
      Sep 2025: INDICATOR_ID, COUNTRY_ID, YEAR, VALUE  (same)
      Older:    may use INDICATORID, COUNTRYID, etc.
    """
    cols = df.columns.tolist()

    def find(candidates):
        for c in candidates:
            if c in cols:
                return c
        return None

    ind_col = find(["INDICATOR_ID", "INDICATORID", "INDICATOR"])
    cty_col = find(["COUNTRY_ID", "COUNTRYID", "GEO_UNIT_ID", "COUNTRY"])
    yr_col  = find(["YEAR", "TIME_PERIOD", "TIME"])
    val_col = find(["VALUE", "OBS_VALUE"])

    if not all([ind_col, cty_col, yr_col, val_col]):
        return None
    return ind_col, cty_col, yr_col, val_col


def uis_bdds_fetch(
    iso_list:     list[str],
    nice:         str,
    uis_code:     str,
    year_min:     int,
    year_max:     int,
    uis_cfg:      dict,
    project_root: Path,
    bdds_file:    str = "both",
    iso_to_name:  dict | None = None,
) -> pd.DataFrame:
    """
    Extract one UIS indicator from BDDS bulk CSV files.

    Parameters
    ----------
    bdds_file : "sdg", "opri", or "both"
        Which zip to search.  Set per-indicator in indicators.yml via
        the bdds_file key to avoid loading 250 MB unnecessarily.
        SDG  indicators: TRTP.1, LR.AG15T99, LR.AG15T24, CR.1.GPIA
        OPRI indicators: NERT.2.CP, NERT.2.GPIA, GER.2.GPIA

    BDDS column layout (February 2026, confirmed):
      INDICATOR_ID  — string (SDG) or integer-as-string (OPRI, normalised)
      COUNTRY_ID    — ISO3 string
      YEAR          — integer
      VALUE         — float
    """
    cache_dir = project_root / uis_cfg.get("bdds_cache_dir", "data/raw/uis")
    timeout   = uis_cfg.get("timeout", 120)
    iso_upper = {c.upper() for c in iso_list}
    bdds_file = (bdds_file or "both").lower()

    # Determine which zip(s) to search
    zip_specs = []
    if bdds_file in ("sdg", "both"):
        zip_specs.append((uis_cfg.get("bdds_sdg_url"),
                          uis_cfg.get("bdds_sdg_csv")))
    if bdds_file in ("opri", "both"):
        zip_specs.append((uis_cfg.get("bdds_opri_url"),
                          uis_cfg.get("bdds_opri_csv")))

    combined_frames: list[pd.DataFrame] = []
    for url, expected_csv in zip_specs:
        if not url:
            continue
        try:
            local  = _download_bdds_zip(url, cache_dir, timeout)
            df_zip = _read_bdds_zip(local, expected_csv=expected_csv)
            if df_zip is not None and not df_zip.empty:
                combined_frames.append(df_zip)
        except Exception as exc:
            print(f"  [warn] BDDS load failed: {exc}")

    if not combined_frames:
        print(f"  [warn] No BDDS data loaded for {nice} ({uis_code}).")
        return pd.DataFrame(columns=["iso3c", "country", "nice", "year", "value"])

    all_data = pd.concat(combined_frames, ignore_index=True)

    cols = _resolve_bdds_columns(all_data)
    if cols is None:
        print(f"  [warn] Cannot map BDDS columns for {nice}. "
              f"Found: {list(all_data.columns[:12])}")
        return pd.DataFrame(columns=["iso3c", "country", "nice", "year", "value"])

    ind_col, cty_col, yr_col, val_col = cols

    yr_numeric = pd.to_numeric(all_data[yr_col], errors="coerce")
    uis_upper  = uis_code.strip().upper()

    mask = (
        (all_data[ind_col] == uis_upper) &
        (all_data[cty_col].astype(str).str.upper().isin(iso_upper)) &
        (yr_numeric >= year_min) &
        (yr_numeric <= year_max)
    )
    subset = all_data.loc[mask, [cty_col, yr_col, val_col]].copy()

    if subset.empty:
        return pd.DataFrame(columns=["iso3c", "country", "nice", "year", "value"])

    subset = subset.rename(columns={cty_col: "iso3c", yr_col: "year", val_col: "value"})
    subset["iso3c"]   = subset["iso3c"].astype(str).str.upper()
    subset["year"]    = pd.to_numeric(subset["year"], errors="coerce").astype("Int64")
    subset["value"]   = pd.to_numeric(subset["value"], errors="coerce")
    subset["nice"]    = nice
    # Map ISO3 → display name using lookup; fall back to ISO3 if not in lookup
    subset["country"] = subset["iso3c"].map(iso_to_name or {}).fillna(subset["iso3c"])

    subset = subset.dropna(subset=["year"])
    subset["year"] = subset["year"].astype(int)

    return subset[["iso3c", "country", "nice", "year", "value"]].reset_index(drop=True)


# ──────────────────────────────────────────────────────────────
# Unified UIS fetch dispatcher
# ──────────────────────────────────────────────────────────────
def uis_fetch(
    iso_list:     list[str],
    nice:         str,
    uis_code:     str,
    year_min:     int,
    year_max:     int,
    uis_cfg:      dict,
    project_root: Path,
    bdds_file:    str = "both",
    iso_to_name:  dict | None = None,
) -> pd.DataFrame:
    """
    Route to API or BDDS mode based on pipeline.yml uis.mode.
    In API mode, reads key from environment variable named in uis.api_key_env.
    bdds_file:   "sdg", "opri", or "both" — which zip to search in BDDS mode.
    iso_to_name: {iso3c: country_name} so BDDS rows carry proper display names.
    """
    mode = uis_cfg.get("mode", "api").lower()

    if mode == "api":
        key_env = uis_cfg.get("api_key_env", "UIS_API_KEY")
        api_key = os.environ.get(key_env, "").strip()
        if not api_key:
            print(f"  [warn] UIS API key not found in env var '{key_env}'. "
                  "Falling back to BDDS mode for this indicator.")
            return uis_bdds_fetch(iso_list, nice, uis_code, year_min, year_max,
                                  uis_cfg, project_root, bdds_file=bdds_file,
                                  iso_to_name=iso_to_name)
        return uis_api_fetch(iso_list, nice, uis_code, year_min, year_max,
                             uis_cfg, api_key)

    elif mode == "bdds":
        return uis_bdds_fetch(iso_list, nice, uis_code, year_min, year_max,
                              uis_cfg, project_root, bdds_file=bdds_file,
                              iso_to_name=iso_to_name)

    else:
        raise ValueError(f"Unknown uis.mode '{mode}'. Must be 'api' or 'bdds'.")


# ──────────────────────────────────────────────────────────────
# Deduplication
# ──────────────────────────────────────────────────────────────
def deduplicate(raw: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    """
    Drop duplicate (iso3c, nice, year) rows keeping first occurrence.
    Duplicates arise when UIS and WDI both provide the same indicator
    (via wb_fallback) for the same country-year.
    """
    key  = ["iso3c", "nice", "year"]
    dup  = raw.duplicated(subset=key, keep=False)
    if dup.any() and verbose:
        print(f"  [dedup] {dup.sum()} duplicate rows removed (keeping first).")
    return raw.drop_duplicates(subset=key, keep="first").reset_index(drop=True)
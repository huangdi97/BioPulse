import hashlib
import json
import logging
import os
import sqlite3
import time
import urllib.request
import urllib.parse
import urllib.error

logger = logging.getLogger(__name__)

_CACHE_DB_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "data",
)
_CACHE_DB_PATH = os.path.join(_CACHE_DB_DIR, "pubmed_cache.db")
_CACHE_TTL = 24 * 3600
_MAX_RETRIES = 2
_RETRY_DELAY = 1

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"


def _get_cache_conn() -> sqlite3.Connection:
    os.makedirs(_CACHE_DB_DIR, exist_ok=True)
    conn = sqlite3.connect(_CACHE_DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS pubmed_cache "
        "(cache_key TEXT PRIMARY KEY, response TEXT, cached_at REAL)"
    )
    return conn


def _cache_key(keyword: str, max_results: int) -> str:
    raw = f"{keyword}|{max_results}"
    return hashlib.md5(raw.encode()).hexdigest()


def _fetch_json(url: str) -> dict | None:
    for attempt in range(_MAX_RETRIES):
        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except (urllib.error.URLError, urllib.error.HTTPError, OSError, json.JSONDecodeError) as e:
            logger.warning("PubMed request failed (attempt %d/%d): %s", attempt + 1, _MAX_RETRIES, e)
            if attempt < _MAX_RETRIES - 1:
                time.sleep(_RETRY_DELAY)
    return None


def search_pubmed(keyword: str, max_results: int = 20) -> list[dict]:
    ckey = _cache_key(keyword, max_results)
    conn = _get_cache_conn()
    row = conn.execute(
        "SELECT response, cached_at FROM pubmed_cache WHERE cache_key = ?", (ckey,)
    ).fetchone()
    if row:
        cached_at = row[1]
        if time.time() - cached_at < _CACHE_TTL:
            return json.loads(row[0])
    pmid_list = _search_ids(keyword, max_results)
    if not pmid_list:
        return []
    papers = _fetch_details(pmid_list)
    conn.execute(
        "INSERT OR REPLACE INTO pubmed_cache (cache_key, response, cached_at) VALUES (?, ?, ?)",
        (ckey, json.dumps(papers), time.time()),
    )
    conn.commit()
    conn.close()
    return papers


def _search_ids(keyword: str, max_results: int) -> list[str]:
    """Search PubMed for PMIDs matching the given keyword.

    Uses NCBI ESearch API with JSON response format.
    Returns a list of PMID strings, or empty list on failure.
    """
    params = urllib.parse.urlencode({
        "db": "pubmed", "term": keyword, "retmax": max_results,
        "retmode": "json",
    })
    data = _fetch_json(f"{ESEARCH_URL}?{params}")
    if not data or "esearchresult" not in data:
        logger.warning("PubMed esearch returned no result for keyword=%s", keyword)
        return []
    idlist = data["esearchresult"].get("idlist", [])
    return idlist


def _fetch_details(pmids: list[str]) -> list[dict]:
    """Fetch detailed paper information for a list of PMIDs.

    Uses NCBI ESummary API to retrieve title, authors, journal, and date.
    Returns a list of paper dicts, or empty list on failure.
    """
    params = urllib.parse.urlencode({
        "db": "pubmed", "id": ",".join(pmids), "retmode": "json",
    })
    data = _fetch_json(f"{ESUMMARY_URL}?{params}")
    if not data or "result" not in data:
        logger.warning("PubMed esummary returned no result for %d IDs", len(pmids))
        return []
    result = data["result"]
    uid_list = result.get("uids", [])
    papers = []
    for uid in uid_list:
        item = result.get(uid, {})
        authors_list = item.get("authors", [])
        authors = [a.get("name", "") for a in authors_list] if isinstance(authors_list, list) else []
        papers.append({
            "pmid": uid,
            "title": item.get("title", ""),
            "authors": authors,
            "journal": (item.get("source", "") or item.get("fulljournalname", "")),
            "pub_date": item.get("pubdate", "") or item.get("pubDate", ""),
            "abstract": "",
            "doi": "",
        })
    return papers

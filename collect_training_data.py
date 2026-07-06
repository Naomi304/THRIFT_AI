"""
collect_training_data.py

Sweeps working marketplace APIs and appends normalized listings to a CSV
for training the THRIFT_AI price predictor.

The output schema unifies asking prices (Amazon, Craigslist) with sold
prices (eBay). Downstream, train_model.py can use `source` as a
categorical feature so the model can learn the offset between
retail-new (Amazon), asking (Craigslist), and sold (eBay) prices.

Usage:
    python collect_training_data.py                          # full sweep, resumable
    python collect_training_data.py --limit 3                # smoke test: 3 combos
    python collect_training_data.py --sources ebay           # eBay only
    python collect_training_data.py --brands Nike,Adidas     # subset
    python collect_training_data.py --no-resume              # ignore checkpoint
"""

import argparse
import csv
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from typing import Callable, Dict, Iterable, List, Optional

from dotenv import load_dotenv

'''add more imports for the new APIs'''
#NOT GOOGLE. API WEIRD AF
from apis.amazon_api import get_amazon_data
from apis.craigslist_api import get_craigslist_data
from apis.ebay_api import get_ebay_data

load_dotenv("apikeys.env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("collect")

BRANDS = [
    "Nike", "Adidas", "H&M", "Zara", "Gap", "Levi's", "Tommy Hilfiger",
    "Calvin Klein", "Ralph Lauren", "Gucci", "Prada", "Burberry",
]

ITEM_TYPES = [
    "t-shirt", "jeans", "jacket", "dress", "shirt", "sweater",
    "pants", "skirt", "blouse", "coat", "shorts", "hoodie",
]

OUTPUT_CSV = "real_training_data.csv"
CHECKPOINT_FILE = ".collection_progress.json"

SCHEMA = [
    "brand", "item_type", "source", "title",
    "sale_price", "shipping_price", "total_price",
    "condition", "location", "date_sold", "url", "image_url",
    "collected_at",
]

# Seconds to sleep AFTER each call. Values sit under RapidAPI BASIC per-second
# caps for each provider.
RATE_LIMITS = {
    "ebay": 1.2,
    "amazon": 1.0,
    "craigslist": 1.0,
}

_PRICE_RE = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?")


def parse_price(value) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = _PRICE_RE.search(str(value))
    if not match:
        return None
    try:
        return float(match.group().replace(",", ""))
    except ValueError:
        return None


def normalize_condition(raw) -> str:
    if not raw:
        return ""
    s = str(raw).strip().lower()
    if "new with tags" in s or "brand new" in s or s in ("new", "new with box"):
        return "new"
    if any(k in s for k in ("pre-owned", "preowned", "used", "second-hand", "secondhand", "vintage")):
        return "used"
    return s


# ---------- Per-source collectors ----------
# Each takes (brand, item_type) and returns partial rows (without shared
# fields brand/item_type/source/collected_at, which sweep() attaches).

def collect_from_ebay(brand: str, item_type: str) -> List[Dict]:
    resp = get_ebay_data(brand=brand, item_type=item_type,
                         size="", color="", material="", condition="")
    if resp.get("status") != "Success":
        log.warning("eBay [%s %s] %s", brand, item_type, str(resp.get("message", ""))[:120])
        return []

    rows = []
    for p in resp.get("products", []):
        sale = parse_price(p.get("price"))
        if sale is None:
            continue
        shipping = parse_price(p.get("shipping")) or 0.0
        rows.append({
            "title": p.get("title", "") or "",
            "sale_price": sale,
            "shipping_price": shipping,
            "total_price": round(sale + shipping, 2),
            "condition": normalize_condition(p.get("condition", "")),
            "location": "",
            "date_sold": p.get("date_sold", "") or "",
            "url": p.get("url", "") or "",
            "image_url": p.get("image", "") or "",
        })
    return rows


def collect_from_amazon(brand: str, item_type: str) -> List[Dict]:
    resp = get_amazon_data(brand=brand, item_type=item_type,
                           size="", color="", material="", condition="")
    if resp.get("status") != "Success":
        log.warning("Amazon [%s %s] %s", brand, item_type, str(resp.get("message", ""))[:120])
        return []

    rows = []
    for p in resp.get("products", []):
        sale = parse_price(p.get("price"))
        if sale is None:
            continue
        rows.append({
            "title": p.get("title", "") or "",
            "sale_price": sale,
            "shipping_price": 0.0,
            "total_price": sale,
            "condition": "new",
            "location": "",
            "date_sold": "",
            "url": p.get("url", "") or "",
            "image_url": p.get("image", "") or "",
        })
    return rows


def collect_from_craigslist(brand: str, item_type: str) -> List[Dict]:
    resp = get_craigslist_data(brand=brand, item_type=item_type,
                               size="", color="", material="", condition="")
    if resp.get("status") != "Success":
        log.warning("Craigslist [%s %s] %s", brand, item_type, str(resp.get("message", ""))[:120])
        return []

    rows = []
    for p in resp.get("products", []):
        sale = parse_price(p.get("price"))
        if sale is None:
            continue
        rows.append({
            "title": p.get("title", "") or "",
            "sale_price": sale,
            "shipping_price": 0.0,
            "total_price": sale,
            "condition": "used",
            "location": p.get("location", "") or "",
            "date_sold": "",
            "url": p.get("url", "") or "",
            "image_url": "",
        })
    return rows


COLLECTORS: Dict[str, Callable[[str, str], List[Dict]]] = {
    "ebay": collect_from_ebay,
    "amazon": collect_from_amazon,
    "craigslist": collect_from_craigslist,
}


# ---------- Persistence ----------

def load_checkpoint(path: str) -> set:
    if not os.path.exists(path):
        return set()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {tuple(item) for item in data.get("completed", [])}
    except Exception as e:
        log.warning("Checkpoint unreadable (%s): %s", path, e)
        return set()


def save_checkpoint(path: str, completed: set) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"completed": sorted([list(t) for t in completed])}, f, indent=2)
    except Exception as e:
        log.warning("Checkpoint unwritable (%s): %s", path, e)


def existing_urls(csv_path: str) -> set:
    if not os.path.exists(csv_path):
        return set()
    urls = set()
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = (row.get("url") or "").strip()
            if url:
                urls.add(url)
    return urls


def append_rows(csv_path: str, rows: List[Dict]) -> None:
    if not rows:
        return
    is_new_file = not os.path.exists(csv_path)
    with open(csv_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SCHEMA, extrasaction="ignore")
        if is_new_file:
            writer.writeheader()
        for row in rows:
            writer.writerow(row)


# ---------- Sweep ----------

def sweep(brands: Iterable[str], items: Iterable[str], sources: List[str],
          output_path: str, checkpoint_path: str,
          resume: bool = True, limit: Optional[int] = None) -> None:

    completed = load_checkpoint(checkpoint_path) if resume else set()
    seen_urls = existing_urls(output_path)

    # Interleave sources per (brand, item_type) so consecutive same-source
    # calls are spaced apart — friendlier to per-second rate limits.
    grid = [(b, i, s) for b in brands for i in items for s in sources]
    if limit is not None:
        grid = grid[:limit]

    log.info("Sweep queued: %d calls across %s", len(grid), sources)
    log.info("Output CSV: %s   Checkpoint: %s   Resume: %s",
             output_path, checkpoint_path, resume)

    added_total = 0
    for idx, (brand, item_type, source) in enumerate(grid, start=1):
        key = (brand, item_type, source)
        if key in completed:
            log.info("[%d/%d] skip (done) %s / %s / %s", idx, len(grid), brand, item_type, source)
            continue

        log.info("[%d/%d] %s / %s / %s", idx, len(grid), brand, item_type, source)
        try:
            rows = COLLECTORS[source](brand, item_type)
        except Exception as e:
            log.error("Collector %s raised: %s", source, e)
            rows = []

        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        new_rows = []
        for r in rows:
            url = (r.get("url") or "").strip()
            if url and url in seen_urls:
                continue
            r["brand"] = brand
            r["item_type"] = item_type
            r["source"] = source
            r["collected_at"] = now
            new_rows.append(r)
            if url:
                seen_urls.add(url)

        append_rows(output_path, new_rows)
        added_total += len(new_rows)
        log.info("     +%d rows  (session total: %d)", len(new_rows), added_total)

        completed.add(key)
        save_checkpoint(checkpoint_path, completed)

        time.sleep(RATE_LIMITS.get(source, 1.0))

    log.info("Sweep complete. %d rows added.", added_total)


# ---------- CLI ----------

def parse_args():
    p = argparse.ArgumentParser(description="Collect real marketplace data for THRIFT_AI training.")
    p.add_argument("--brands", help="Comma-separated brand subset (default: built-in list)")
    p.add_argument("--items", help="Comma-separated item_type subset (default: built-in list)")
    p.add_argument("--sources", default="ebay,amazon,craigslist",
                   help="Comma-separated sources (default: ebay,amazon,craigslist)")
    p.add_argument("--limit", type=int, help="Cap total combos (for testing)")
    p.add_argument("--out", default=OUTPUT_CSV, help="Output CSV path")
    p.add_argument("--checkpoint", default=CHECKPOINT_FILE, help="Checkpoint file path")
    p.add_argument("--no-resume", action="store_true", help="Ignore checkpoint")
    return p.parse_args()


def main():
    if not os.getenv("API_KEY"):
        log.error("API_KEY missing. Check apikeys.env.")
        sys.exit(1)

    args = parse_args()

    brands = [b.strip() for b in args.brands.split(",")] if args.brands else BRANDS
    items = [i.strip() for i in args.items.split(",")] if args.items else ITEM_TYPES
    sources = [s.strip() for s in args.sources.split(",")]

    unknown = [s for s in sources if s not in COLLECTORS]
    if unknown:
        log.error("Unknown source(s): %s. Available: %s", unknown, list(COLLECTORS))
        sys.exit(1)

    sweep(brands=brands, items=items, sources=sources,
          output_path=args.out, checkpoint_path=args.checkpoint,
          resume=not args.no_resume, limit=args.limit)


if __name__ == "__main__":
    main()

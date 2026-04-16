#!/usr/bin/env python3
"""
company-filter-refresh: 完整数据集刷新工具

子命令:
  search    从公开数据源搜索公司（YC Companies、Google、GitHub Awesome Lists）
  discover  从公司官网 /about /team 页自动发现高管
  enrich    从 RocketReach/Apollo/Hunter.io 等补充联系方式
  email     根据姓名+域名批量推断邮箱
  import    从外部 CSV 导入
  merge     合并另一个 CSV 到现有数据
  refresh   一键编排（search → discover → email → enrich）
  status    数据集状态 + 覆盖率 + 建议

依赖: pip install requests beautifulsoup4 (search/discover/enrich 需要)
import/merge/email/status 无外部依赖。

Usage:
  python3 refresh.py search --query "Trimble resellers USA" --limit 20
  python3 refresh.py search --source yc --industry fintech --region US --limit 50
  python3 refresh.py search --source google --query "Leica authorized dealer surveying US"
  python3 refresh.py search --source awesome --topic surveying

  python3 refresh.py discover
  python3 refresh.py discover --company "AllTerra Central"

  python3 refresh.py enrich
  python3 refresh.py enrich --company "AllTerra Central"
  python3 refresh.py enrich --source rocketreach

  python3 refresh.py email
  python3 refresh.py email --pattern "{first}@{domain}"

  python3 refresh.py import companies --file x.csv --mapping name=Organization,region=HQ
  python3 refresh.py import executives --file x.csv

  python3 refresh.py merge companies --file x.csv
  python3 refresh.py merge executives --file x.csv

  python3 refresh.py refresh --mode full
  python3 refresh.py refresh --mode companies
  python3 refresh.py refresh --mode executives
  python3 refresh.py refresh --mode targeted --industry FinTech

  python3 refresh.py status
"""

import csv
import sys
import os
import re
import json
import argparse
import time
import shutil
import io
import threading
from contextlib import redirect_stdout, redirect_stderr
from datetime import date
from urllib.parse import quote_plus, urljoin, urlparse

APP_NAME = "Charlie Skill"


def _source_data_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "company-filter", "data")
    )


def _packaged_data_home():
    if sys.platform == "darwin":
        return os.path.expanduser(f"~/Library/Application Support/{APP_NAME}/data")
    if os.name == "nt":
        appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(appdata, APP_NAME, "data")
    return os.path.expanduser(f"~/.local/share/{APP_NAME}/data")


def _seed_data_dir():
    if getattr(sys, "frozen", False):
        bundle_root = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        return os.path.join(bundle_root, "seed_data")
    return _source_data_dir()


def _ensure_runtime_data_dir():
    runtime_dir = _packaged_data_home() if getattr(sys, "frozen", False) else _source_data_dir()
    os.makedirs(runtime_dir, exist_ok=True)

    seed_dir = _seed_data_dir()
    for filename in ("companies.csv", "executives.csv", "last_updated.txt", ".gitkeep"):
        target = os.path.join(runtime_dir, filename)
        seed = os.path.join(seed_dir, filename)
        if not os.path.exists(target) and os.path.exists(seed):
            shutil.copy2(seed, target)

    return runtime_dir


DATA_DIR = _ensure_runtime_data_dir()
COMPANIES = os.path.join(DATA_DIR, "companies.csv")
EXECUTIVES = os.path.join(DATA_DIR, "executives.csv")
UPDATED_FILE = os.path.join(DATA_DIR, "last_updated.txt")

COMPANY_FIELDS = [
    "name","brand","region","website","description","source","updated_at"
]
EXECUTIVE_FIELDS = [
    "company_name","brand","headquarters","executive_name","title",
    "role_level","linkedin_url","email_work","phone","confidence","updated_at"
]

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════

def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_csv(path, rows, fieldnames):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

def update_timestamp(target):
    lines = {}
    if os.path.exists(UPDATED_FILE):
        with open(UPDATED_FILE) as f:
            for l in f:
                if "=" in l:
                    k, v = l.strip().split("=", 1)
                    lines[k] = v
    lines[target] = date.today().isoformat()
    with open(UPDATED_FILE, "w") as f:
        for k, v in lines.items():
            f.write(f"{k}={v}\n")

def normalize_name(name):
    return re.sub(r'[^a-z0-9]', '', name.lower().strip())

def col(width, text):
    text = str(text or "")
    if len(text) > width:
        text = text[:width-1] + "…"
    return text.ljust(width)

def print_table(rows, columns):
    if not rows:
        print("  (no results)")
        return
    header = "  ".join(col(w, h) for h, _, w in columns)
    sep    = "  ".join("-" * w for _, _, w in columns)
    print(header)
    print(sep)
    for r in rows:
        print("  ".join(col(w, r.get(f, "")) for _, f, w in columns))
    print(f"\n{len(rows)} record(s)")

def infer_role_level(title):
    t = title.lower()
    for kw in ["chief","ceo","cto","cfo","coo","cmo","cpo","cro",
               "founder","co-founder","president","owner","managing partner",
               "executive partner"]:
        if kw in t:
            return "C"
    for kw in ["vice president","vp ","vp,","evp","svp"]:
        if kw in t:
            return "VP"
    for kw in ["director","head of"]:
        if kw in t:
            return "D"
    return ""

def domain_from_website(website):
    w = website.strip().lower()
    w = re.sub(r'^https?://', '', w)
    w = re.sub(r'/.*$', '', w)
    w = re.sub(r'^www\.', '', w)
    return w

def parse_mapping(mapping_str):
    if not mapping_str:
        return {}
    return dict(p.split("=") for p in mapping_str.split(",") if "=" in p)

def _require_deps():
    """Check optional deps, return (requests, BeautifulSoup) or exit."""
    try:
        import requests
        from bs4 import BeautifulSoup
        return requests, BeautifulSoup
    except ImportError:
        print("Error: search/discover/enrich require additional dependencies.")
        print("Run: pip install requests beautifulsoup4")
        sys.exit(1)

def _fetch(requests, url, timeout=15):
    """Fetch URL with error handling, return text or None."""
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"  ⚠️  Failed to fetch {url}: {e}")
        return None

def _upsert_company(existing, existing_keys, row):
    key = normalize_name(row.get("name",""))
    if not key:
        return False
    row["updated_at"] = date.today().isoformat()
    if key in existing_keys:
        idx = existing_keys[key]
        for f in COMPANY_FIELDS:
            if row.get(f,"").strip() and not existing[idx].get(f,"").strip():
                existing[idx][f] = row[f]
        return False  # updated, not new
    else:
        existing.append(row)
        existing_keys[key] = len(existing) - 1
        return True  # new

def _upsert_executive(existing, existing_keys, row):
    key = (normalize_name(row.get("company_name","")),
           normalize_name(row.get("executive_name","")))
    if not key[0] or not key[1]:
        return False
    row["updated_at"] = date.today().isoformat()
    if not row.get("role_level") and row.get("title"):
        row["role_level"] = infer_role_level(row["title"])
    if key in existing_keys:
        idx = existing_keys[key]
        for f in EXECUTIVE_FIELDS:
            if row.get(f,"").strip() and not existing[idx].get(f,"").strip():
                existing[idx][f] = row[f]
        return False
    else:
        existing.append(row)
        existing_keys[key] = len(existing) - 1
        return True


# ══════════════════════════════════════════════════════════════════════════════
# search — 从公开数据源搜索公司
# ══════════════════════════════════════════════════════════════════════════════

def cmd_search(args):
    requests, BeautifulSoup = _require_deps()

    source = args.source or "auto"
    all_results = []

    if source == "auto":
        # Run all sources, accumulate results
        print("═══ Auto search: trying all sources ═══\n")

        # 1. DuckDuckGo with query variants
        if args.query:
            ddg = _search_duckduckgo(requests, BeautifulSoup, args)
            all_results.extend(ddg)

        # 2. YC if industry given
        if args.industry or args.query:
            yc = _search_yc(requests, args)
            all_results.extend(yc)

        # 3. Bing
        if args.query:
            bing = _search_bing(requests, BeautifulSoup, args)
            all_results.extend(bing)

        # 4. If large limit, auto-expand with query variants
        if args.limit and args.limit > 50 and args.query:
            variants = _generate_query_variants(args.query)
            for v in variants:
                if len(all_results) >= args.limit:
                    break
                print(f"\n── Variant query: \"{v}\" ──")
                vargs = argparse.Namespace(**vars(args))
                vargs.query = v
                ddg = _search_duckduckgo(requests, BeautifulSoup, vargs)
                all_results.extend(ddg)
                time.sleep(2)

    elif source == "duckduckgo":
        all_results = _search_duckduckgo(requests, BeautifulSoup, args)
    elif source == "bing":
        all_results = _search_bing(requests, BeautifulSoup, args)
    elif source == "yc":
        all_results = _search_yc(requests, args)
    elif source == "awesome":
        all_results = _search_awesome(requests, BeautifulSoup, args)
    elif source == "google":
        all_results = _search_google(requests, BeautifulSoup, args)
    else:
        print(f"Unknown source: {source}. Options: auto, duckduckgo, bing, yc, awesome, google")
        return

    if not all_results:
        print("No results found.")
        return

    # dedupe by normalized name before merge
    seen = set()
    unique = []
    for r in all_results:
        key = normalize_name(r.get("name",""))
        if key and key not in seen:
            seen.add(key)
            unique.append(r)

    # merge into companies.csv
    existing = read_csv(COMPANIES)
    existing_keys = {normalize_name(r["name"]): i for i, r in enumerate(existing)}
    added = sum(1 for r in unique if _upsert_company(existing, existing_keys, r))
    write_csv(COMPANIES, existing, COMPANY_FIELDS)
    update_timestamp("companies")

    print(f"\n✓ Search complete: {len(unique)} unique found, +{added} new, {len(existing)} total")

def _generate_query_variants(base_query):
    """Generate search query variants to maximize coverage."""
    words = base_query.split()
    variants = []

    # state-specific variants
    us_states = [
        "California","Texas","Florida","New York","Illinois","Pennsylvania",
        "Ohio","Georgia","North Carolina","Michigan","New Jersey","Virginia",
        "Washington","Arizona","Massachusetts","Tennessee","Indiana","Missouri",
        "Maryland","Wisconsin","Colorado","Minnesota","South Carolina","Alabama",
        "Louisiana","Kentucky","Oregon","Oklahoma","Connecticut","Utah","Iowa",
        "Nevada","Arkansas","Mississippi","Kansas","Nebraska","Idaho","New Mexico",
        "West Virginia","Hawaii","New Hampshire","Maine","Montana","Rhode Island",
        "Delaware","South Dakota","North Dakota","Alaska","Vermont","Wyoming",
    ]
    for state in us_states:
        variants.append(f"{base_query} {state}")

    # synonym variants
    synonyms = {
        "reseller":    ["dealer","distributor","partner","supplier","vendor","retailer"],
        "authorized":  ["certified","official","approved","licensed"],
        "USA":         ["United States","US","America"],
    }
    for word in words:
        wl = word.lower()
        if wl in synonyms:
            for syn in synonyms[wl]:
                v = base_query.replace(word, syn)
                if v not in variants:
                    variants.append(v)

    return variants

def _search_yc(requests, args):
    """Search YC Companies via Algolia public API."""
    print(f"🔍 Searching YC Companies...")
    url = "https://45bwzj1sgc-dsn.algolia.net/1/indexes/YCCompany_production/query"
    params = {
        "x-algolia-application-id": "45BWZJ1SGC",
        "x-algolia-api-key": "MjBjYjRiMzY0NzdhZWY0NjExY2NhZjYxMGIxYjc2MTAwNWFkNTkwNTc4NjgxYjU0YzFhYTY2ZGQ5OGY5NDMxZnJlc3RyaWN0SW5kaWNlcz0lNUIlMjJZQ0NvbXBhbnlfcHJvZHVjdGlvbiUyMiU1RCZ0YWdGaWx0ZXJzPSU1QiUyMiUyMiU1RCZhbmFseXRpY3NUYWdzPSU1QiUyMnljZGMlMjIlNUQ="
    }
    query = args.query or args.industry or ""
    limit = min(args.limit or 20, 100)

    body = {"query": query, "hitsPerPage": limit, "page": 0}

    # Add facet filters
    facet_filters = []
    if args.region:
        facet_filters.append(f"regions:{args.region}")
    if facet_filters:
        body["facetFilters"] = [facet_filters]

    try:
        r = requests.post(url, params=params, json=body, timeout=15)
        data = r.json()
    except Exception as e:
        print(f"  ⚠️  YC API failed: {e}")
        return []

    results = []
    for hit in data.get("hits", []):
        results.append({
            "name":        hit.get("name",""),
            "industry":    hit.get("industries",[""])[0] if hit.get("industries") else "",
            "region":      ", ".join(hit.get("regions",[])),
            "website":     hit.get("website",""),
            "description": hit.get("one_liner",""),
            "stage":       hit.get("status",""),
            "size":        hit.get("team_size_str",""),
            "source":      "YC Companies",
        })
        print(f"  + {hit.get('name','')} — {hit.get('one_liner','')[:60]}")

    return results

def _search_duckduckgo(requests, BeautifulSoup, args):
    """Search via DuckDuckGo HTML (reliable, no blocking)."""
    query = args.query
    if not query:
        print("Error: --query required")
        return []

    limit = min(args.limit or 20, 200)  # DDG per-query cap
    print(f"🔍 DuckDuckGo: \"{query}\" (limit {limit})...")

    results = []
    page_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"

    pages_fetched = 0
    max_pages = max(1, limit // 10)

    while len(results) < limit and pages_fetched < max_pages:
        html = _fetch(requests, page_url, timeout=20)
        if not html:
            break

        soup = BeautifulSoup(html, "html.parser")
        found = False

        for item in soup.find_all("div", class_="result"):
            a = item.find("a", class_="result__a")
            snippet_el = item.find("a", class_="result__snippet")

            if not a:
                continue

            href = a.get("href","")
            title = a.get_text(strip=True)
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""

            # resolve DDG redirect URLs
            if "uddg=" in href:
                m = re.search(r'uddg=([^&]+)', href)
                if m:
                    from urllib.parse import unquote
                    href = unquote(m.group(1))

            parsed = urlparse(href)
            domain = parsed.netloc.replace("www.", "")

            skip_domains = ["google.com","youtube.com","wikipedia.org",
                          "linkedin.com","twitter.com","facebook.com",
                          "reddit.com","amazon.com","yelp.com",
                          "duckduckgo.com","bbb.org"]
            if any(d in domain for d in skip_domains):
                continue
            if not domain or len(domain) < 4:
                continue

            company_name = title.split("|")[0].split("-")[0].split("–")[0].split("—")[0].strip()
            if not company_name or len(company_name) < 2:
                continue

            results.append({
                "name":        company_name,
                "website":     domain,
                "description": snippet[:200],
                "source":      "DuckDuckGo",
            })
            print(f"  + {company_name} ({domain})")
            found = True

            if len(results) >= limit:
                break

        # find next page button
        next_form = soup.find("input", {"value": "Next"})
        if next_form and found:
            form = next_form.find_parent("form")
            if form:
                inputs = {inp.get("name",""): inp.get("value","")
                         for inp in form.find_all("input") if inp.get("name")}
                qs = "&".join(f"{k}={quote_plus(v)}" for k,v in inputs.items())
                page_url = f"https://html.duckduckgo.com/html/?{qs}"
            else:
                break
        else:
            break

        pages_fetched += 1
        time.sleep(1.5)

    return results

def _search_bing(requests, BeautifulSoup, args):
    """Search via Bing (fallback, less aggressive blocking)."""
    query = args.query
    if not query:
        return []

    limit = min(args.limit or 20, 100)
    print(f"🔍 Bing: \"{query}\" (limit {limit})...")

    results = []
    page = 0
    while len(results) < limit:
        offset = page * 10
        url = f"https://www.bing.com/search?q={quote_plus(query)}&first={offset+1}"
        html = _fetch(requests, url, timeout=15)
        if not html:
            break

        soup = BeautifulSoup(html, "html.parser")
        found = False

        for li in soup.find_all("li", class_="b_algo"):
            a = li.find("a", href=True)
            if not a:
                continue

            href = a.get("href","")
            title = a.get_text(strip=True)

            p = li.find("p")
            snippet = p.get_text(strip=True) if p else ""

            parsed = urlparse(href)
            domain = parsed.netloc.replace("www.", "")

            skip_domains = ["google.com","youtube.com","wikipedia.org",
                          "linkedin.com","twitter.com","facebook.com",
                          "reddit.com","amazon.com","bing.com","yelp.com"]
            if any(d in domain for d in skip_domains):
                continue
            if not domain or len(domain) < 4:
                continue

            company_name = title.split("|")[0].split("-")[0].split("–")[0].split("—")[0].strip()
            if not company_name or len(company_name) < 2:
                continue

            results.append({
                "name":        company_name,
                "website":     domain,
                "description": snippet[:200],
                "source":      "Bing",
            })
            print(f"  + {company_name} ({domain})")
            found = True

            if len(results) >= limit:
                break

        if not found:
            break
        page += 1
        time.sleep(2)

    return results

def _search_google(requests, BeautifulSoup, args):
    """Search via Google (may be rate limited / blocked)."""
    query = args.query
    if not query:
        return []

    limit = min(args.limit or 10, 50)
    print(f"🔍 Google: \"{query}\" (limit {limit}, may be blocked)...")

    results = []
    page = 0
    while len(results) < limit:
        url = f"https://www.google.com/search?q={quote_plus(query)}&start={page*10}"
        html = _fetch(requests, url)
        if not html:
            break

        soup = BeautifulSoup(html, "html.parser")
        found = False
        for div in soup.find_all("div", class_="g"):
            a = div.find("a", href=True)
            h3 = div.find("h3")
            if not a or not h3:
                continue

            href = a["href"]
            title = h3.get_text(strip=True)
            parsed = urlparse(href)
            domain = parsed.netloc.replace("www.", "")

            skip_domains = ["google.com","youtube.com","wikipedia.org",
                          "linkedin.com","twitter.com","facebook.com",
                          "reddit.com","amazon.com"]
            if any(d in domain for d in skip_domains):
                continue

            company_name = title.split("|")[0].split("-")[0].split("–")[0].strip()
            results.append({
                "name":        company_name,
                "website":     domain,
                "source":      "Google",
            })
            print(f"  + {company_name} ({domain})")
            found = True
            if len(results) >= limit:
                break

        if not found:
            break
        page += 1
        time.sleep(3)

    return results

def _search_awesome(requests, BeautifulSoup, args):
    """Search GitHub Awesome Lists for companies in a topic."""
    topic = args.topic or args.query or args.industry
    if not topic:
        print("Error: --topic or --query required for awesome source")
        return []

    topic_slug = topic.lower().replace(" ", "-")
    url = f"https://raw.githubusercontent.com/sindresorhus/awesome/main/readme.md"
    print(f"🔍 Searching GitHub Awesome Lists for: {topic}...")

    # Try direct awesome-{topic} repo first
    readme_url = f"https://raw.githubusercontent.com/awesome-{topic_slug}/{topic_slug}/main/README.md"
    html = _fetch(requests, readme_url)
    if not html:
        readme_url = f"https://raw.githubusercontent.com/sindresorhus/awesome-{topic_slug}/main/readme.md"
        html = _fetch(requests, readme_url)
    if not html:
        print(f"  No awesome list found for '{topic}'")
        return []

    # parse markdown links as companies
    results = []
    limit = args.limit or 50
    for match in re.finditer(r'\[([^\]]+)\]\((https?://[^\)]+)\)', html):
        name = match.group(1).strip()
        url_val = match.group(2).strip()
        if len(name) < 3 or len(name) > 60:
            continue

        parsed = urlparse(url_val)
        domain = parsed.netloc.replace("www.", "")

        skip = ["github.com","wikipedia.org","youtube.com","twitter.com",
                "linkedin.com","medium.com"]
        if any(d in domain for d in skip):
            continue

        results.append({
            "name":    name,
            "website": domain,
            "source":  f"GitHub Awesome-{topic}",
        })
        print(f"  + {name} ({domain})")
        if len(results) >= limit:
            break

    return results


# ══════════════════════════════════════════════════════════════════════════════
# discover — 从公司官网发现高管
# ══════════════════════════════════════════════════════════════════════════════

ABOUT_PATHS = [
    "/about", "/about-us", "/about/", "/about-us/",
    "/team", "/team/", "/our-team", "/our-team/",
    "/leadership", "/leadership/", "/management",
    "/people", "/company", "/company/about",
]

TITLE_PATTERNS = [
    r"(?:Chief\s+\w+\s+Officer|C[ETFOMPR]O)\b",
    r"\b(?:President|Founder|Co-Founder|Owner)\b",
    r"\bVice\s+President\b", r"\bVP\s+(?:of\s+)?\w+",
    r"\b(?:EVP|SVP)\b",
    r"\bDirector\s+(?:of\s+)?\w+",
    r"\bHead\s+of\s+\w+",
    r"\bGeneral\s+Manager\b", r"\bManaging\s+(?:Director|Partner)\b",
]

def cmd_discover(args):
    requests, BeautifulSoup = _require_deps()

    companies = read_csv(COMPANIES)
    executives = read_csv(EXECUTIVES)
    exec_keys = {(normalize_name(r["company_name"]), normalize_name(r["executive_name"])): i
                 for i, r in enumerate(executives)}

    if args.company:
        companies = [c for c in companies if args.company.lower() in c.get("name","").lower()]

    if not companies:
        print("No companies to discover. Run 'search' first.")
        return

    total_added = 0

    for c in companies:
        website = c.get("website","").strip()
        if not website:
            continue

        if not website.startswith("http"):
            website = f"https://{website}"

        name = c.get("name","")
        print(f"\n🔍 {name} ({website})")

        found_any = False
        for path in ABOUT_PATHS:
            url = urljoin(website, path)
            html = _fetch(requests, url, timeout=10)
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text(" ", strip=True)

            # find name-title pairs near title keywords
            people = _extract_people(soup, text, name)
            if people:
                found_any = True
                for person in people:
                    row = {
                        "company_name":   c.get("name",""),
                        "brand":          c.get("brand",""),
                        "headquarters":   c.get("region",""),
                        "executive_name": person["name"],
                        "title":          person["title"],
                        "confidence":     "medium",
                        "source":         f"Website {path}",
                    }
                    if _upsert_executive(executives, exec_keys, row):
                        total_added += 1
                        print(f"  + {person['name']} — {person['title']}")
                    else:
                        print(f"  = {person['name']} — {person['title']} (exists)")
                break  # found people on this path, skip rest

        if not found_any:
            print(f"  (no leadership page found)")

        time.sleep(1)  # rate limit

    write_csv(EXECUTIVES, executives, EXECUTIVE_FIELDS)
    update_timestamp("executives")
    print(f"\n✓ Discover complete: +{total_added} new executives")

def _extract_people(soup, text, company_name):
    """Try to extract name-title pairs from page content."""
    people = []
    seen = set()

    # Strategy 1: structured HTML (h2/h3/h4 + p or span)
    for tag in soup.find_all(["h2","h3","h4","strong","b"]):
        tag_text = tag.get_text(strip=True)
        if len(tag_text) < 3 or len(tag_text) > 60:
            continue

        # check if next sibling or parent has a title
        next_el = tag.find_next_sibling()
        if next_el:
            next_text = next_el.get_text(strip=True)
        else:
            parent = tag.parent
            next_text = parent.get_text(strip=True) if parent else ""

        for pattern in TITLE_PATTERNS:
            match = re.search(pattern, next_text, re.IGNORECASE)
            if match:
                title_str = _clean_title(next_text, match)
                name_str = _clean_name(tag_text, company_name)
                if name_str and title_str and name_str not in seen:
                    people.append({"name": name_str, "title": title_str})
                    seen.add(name_str)
                break

            match = re.search(pattern, tag_text, re.IGNORECASE)
            if match:
                # title is in the tag, name might be in next element
                if next_el:
                    candidate = next_el.get_text(strip=True)
                    name_str = _clean_name(candidate, company_name)
                    title_str = _clean_title(tag_text, match)
                    if name_str and title_str and name_str not in seen:
                        people.append({"name": name_str, "title": title_str})
                        seen.add(name_str)
                break

    # Strategy 2: regex on full text — "Name, Title" or "Name — Title"
    if not people:
        for pattern in TITLE_PATTERNS:
            for m in re.finditer(
                rf'([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[,\-–—|]\s*({pattern}[^.\n,]*)',
                text, re.IGNORECASE
            ):
                name_str = _clean_name(m.group(1), company_name)
                title_str = m.group(2).strip().rstrip(".")
                if name_str and title_str and len(name_str.split()) >= 2 and name_str not in seen:
                    people.append({"name": name_str, "title": title_str})
                    seen.add(name_str)

    return people[:10]  # cap at 10

def _clean_name(text, company_name):
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    if company_name.lower() in text.lower():
        return ""
    if len(text) < 4 or len(text) > 50:
        return ""
    if not re.match(r'^[A-Z]', text):
        return ""
    # must have at least 2 words
    if len(text.split()) < 2:
        return ""
    # remove trailing punctuation
    text = text.rstrip(".,;:-–—")
    return text

def _clean_title(text, match):
    # extract the matched title + a few trailing words
    start = match.start()
    end = min(len(text), match.end() + 30)
    title = text[start:end]
    # cut at sentence boundary
    title = re.split(r'[.\n]', title)[0].strip()
    title = title.rstrip(".,;:-–—")
    return title if len(title) > 2 else ""


# ══════════════════════════════════════════════════════════════════════════════
# enrich — 从 B2B 数据平台补充联系方式
# ══════════════════════════════════════════════════════════════════════════════

def cmd_enrich(args):
    requests, BeautifulSoup = _require_deps()

    executives = read_csv(EXECUTIVES)
    companies = {r["name"]: r for r in read_csv(COMPANIES)}
    source = args.source or "all"

    if args.company:
        targets = [e for e in executives if args.company.lower() in e.get("company_name","").lower()]
    else:
        targets = executives

    if not targets:
        print("No executives to enrich.")
        return

    updated = 0
    for e in targets:
        name = e.get("executive_name","")
        company = e.get("company_name","")
        c = companies.get(company, {})
        domain = domain_from_website(c.get("website",""))

        if not name or not company:
            continue

        enriched = False

        # RocketReach (public preview)
        if source in ("all", "rocketreach") and not e.get("email_work"):
            result = _enrich_rocketreach(requests, BeautifulSoup, name, company)
            if result:
                for k, v in result.items():
                    if v and not e.get(k,"").strip():
                        e[k] = v
                        enriched = True

        # Google search for contact info
        if source in ("all", "google"):
            result = _enrich_google(requests, BeautifulSoup, name, company)
            if result:
                for k, v in result.items():
                    if v and not e.get(k,"").strip():
                        e[k] = v
                        enriched = True

        if enriched:
            e["updated_at"] = date.today().isoformat()
            if e.get("confidence","") == "low":
                e["confidence"] = "medium"
            updated += 1
            print(f"  ✓ {name} ({company}): enriched")
        else:
            print(f"  - {name} ({company}): no new data")

        time.sleep(2)  # rate limit

    write_csv(EXECUTIVES, executives, EXECUTIVE_FIELDS)
    update_timestamp("executives")
    print(f"\n✓ Enrich complete: {updated}/{len(targets)} updated")

def _enrich_rocketreach(requests, BeautifulSoup, name, company):
    """Try to get info from RocketReach public preview."""
    query = f"{name} {company}"
    url = f"https://rocketreach.co/search?searchFilter=name&keyword={quote_plus(query)}"
    html = _fetch(requests, url, timeout=10)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    result = {}

    # look for email patterns in text
    text = soup.get_text(" ", strip=True)
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    if emails:
        result["email_work"] = emails[0]

    # look for linkedin URLs
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "linkedin.com/in/" in href:
            result["linkedin_url"] = href
            break

    return result if result else None

def _enrich_google(requests, BeautifulSoup, name, company):
    """Search Google for contact info."""
    query = f'"{name}" "{company}" email OR phone OR contact'
    url = f"https://www.google.com/search?q={quote_plus(query)}"
    html = _fetch(requests, url, timeout=10)
    if not html:
        return None

    text = html  # search in raw HTML
    result = {}

    # find emails
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    skip_emails = ["example.com","google.com","gmail.com","yahoo.com","sentry.io"]
    for e in emails:
        if not any(s in e for s in skip_emails):
            result["email_work"] = e
            break

    # find phone numbers
    phones = re.findall(r'[\(]?\d{3}[\)]?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    if phones:
        result["phone"] = phones[0]

    # find linkedin
    li_match = re.search(r'https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+', text)
    if li_match:
        result["linkedin_url"] = li_match.group(0)

    return result if result else None


# ══════════════════════════════════════════════════════════════════════════════
# email — 批量推断邮箱
# ══════════════════════════════════════════════════════════════════════════════

EMAIL_PATTERNS = [
    "{first}.{last}@{domain}",
    "{first}@{domain}",
    "{first_initial}{last}@{domain}",
    "{first}{last}@{domain}",
    "{first}_{last}@{domain}",
    "{last}@{domain}",
]

def cmd_email(args):
    companies = {r["name"]: r for r in read_csv(COMPANIES)}
    executives = read_csv(EXECUTIVES)
    pattern = args.pattern or "{first}.{last}@{domain}"
    updated, skipped = 0, 0

    for e in executives:
        if args.company and args.company.lower() not in e.get("company_name","").lower():
            continue
        if e.get("email_work","").strip():
            skipped += 1
            continue

        c = companies.get(e.get("company_name",""), {})
        website = c.get("website","")
        if not website:
            continue

        domain = domain_from_website(website)
        name = e.get("executive_name","")
        parts = name.strip().split()
        if len(parts) < 2:
            continue

        first = re.sub(r'[^a-z]', '', parts[0].lower())
        last  = re.sub(r'[^a-z]', '', parts[-1].lower())
        if not first or not last:
            continue

        email = pattern.format(first=first, last=last,
                               first_initial=first[0], domain=domain)
        e["email_work"] = email
        if e.get("confidence","") not in ("high",):
            e["confidence"] = "low"
        updated += 1

    write_csv(EXECUTIVES, executives, EXECUTIVE_FIELDS)
    update_timestamp("executives")
    print(f"✓ Email generation: {updated} generated, {skipped} skipped (already has email)")
    if not args.pattern:
        print(f"\nCommon patterns:")
        for p in EMAIL_PATTERNS:
            print(f"  python3 refresh.py email --pattern \"{p}\"")


# ══════════════════════════════════════════════════════════════════════════════
# import — 从外部 CSV 导入
# ══════════════════════════════════════════════════════════════════════════════

def cmd_import(args):
    if not os.path.exists(args.file):
        print(f"Error: file not found: {args.file}")
        sys.exit(1)

    mapping = parse_mapping(args.mapping)

    with open(args.file, newline="", encoding="utf-8") as f:
        source_rows = list(csv.DictReader(f))

    if not source_rows:
        print("Error: source file is empty")
        sys.exit(1)

    print(f"Source: {len(source_rows)} rows from {args.file}")
    if mapping:
        print(f"Mapping: {mapping}")

    if args.target == "companies":
        existing = read_csv(COMPANIES)
        existing_keys = {normalize_name(r["name"]): i for i, r in enumerate(existing)}
        added = 0
        for sr in source_rows:
            row = {}
            for f in COMPANY_FIELDS:
                src_col = mapping.get(f, f)
                row[f] = sr.get(src_col, "").strip()
            row.setdefault("source", os.path.basename(args.file))
            if _upsert_company(existing, existing_keys, row):
                added += 1
        write_csv(COMPANIES, existing, COMPANY_FIELDS)
        update_timestamp("companies")
        print(f"✓ Import: +{added} new, {len(existing)} total")
    else:
        existing = read_csv(EXECUTIVES)
        existing_keys = {(normalize_name(r["company_name"]), normalize_name(r["executive_name"])): i
                        for i, r in enumerate(existing)}
        added = 0
        for sr in source_rows:
            row = {}
            for f in EXECUTIVE_FIELDS:
                src_col = mapping.get(f, f)
                row[f] = sr.get(src_col, "").strip()
            row.setdefault("confidence", "medium")
            row.setdefault("source", os.path.basename(args.file))
            if _upsert_executive(existing, existing_keys, row):
                added += 1
        write_csv(EXECUTIVES, existing, EXECUTIVE_FIELDS)
        update_timestamp("executives")
        print(f"✓ Import: +{added} new, {len(existing)} total")


# ══════════════════════════════════════════════════════════════════════════════
# merge — 合并 CSV
# ══════════════════════════════════════════════════════════════════════════════

def cmd_merge(args):
    if not os.path.exists(args.file):
        print(f"Error: file not found: {args.file}")
        sys.exit(1)

    with open(args.file, newline="", encoding="utf-8") as f:
        source_rows = list(csv.DictReader(f))

    if args.target == "companies":
        existing = read_csv(COMPANIES)
        existing_keys = {normalize_name(r["name"]): i for i, r in enumerate(existing)}
        added = sum(1 for r in source_rows if _upsert_company(existing, existing_keys, r))
        write_csv(COMPANIES, existing, COMPANY_FIELDS)
        update_timestamp("companies")
    else:
        existing = read_csv(EXECUTIVES)
        existing_keys = {(normalize_name(r["company_name"]), normalize_name(r["executive_name"])): i
                        for i, r in enumerate(existing)}
        added = sum(1 for r in source_rows if _upsert_executive(existing, existing_keys, r))
        write_csv(EXECUTIVES, existing, EXECUTIVE_FIELDS)
        update_timestamp("executives")

    print(f"✓ Merge: +{added} new, {len(existing)} total")


# ══════════════════════════════════════════════════════════════════════════════
# run — 一条命令全自动
# ══════════════════════════════════════════════════════════════════════════════

US_STATES = [
    "Alabama","Alaska","Arizona","Arkansas","California","Colorado","Connecticut",
    "Delaware","Florida","Georgia","Hawaii","Idaho","Illinois","Indiana","Iowa",
    "Kansas","Kentucky","Louisiana","Maine","Maryland","Massachusetts","Michigan",
    "Minnesota","Mississippi","Missouri","Montana","Nebraska","Nevada",
    "New Hampshire","New Jersey","New Mexico","New York","North Carolina",
    "North Dakota","Ohio","Oklahoma","Oregon","Pennsylvania","Rhode Island",
    "South Carolina","South Dakota","Tennessee","Texas","Utah","Vermont",
    "Virginia","Washington","West Virginia","Wisconsin","Wyoming",
]

US_REGIONS = [
    "Northeast", "Southeast", "Midwest", "Southwest", "West Coast",
    "Pacific Northwest", "Mountain West", "Great Plains", "Mid-Atlantic",
    "New England", "Gulf Coast", "Rocky Mountain",
]

QUERY_SYNONYMS = {
    "reseller":   ["dealer","distributor","partner","supplier","vendor","retailer","outlet"],
    "authorized": ["certified","official","approved","licensed","registered"],
    "dealer":     ["reseller","distributor","supplier","vendor","partner"],
}

def _build_search_plan(base_query):
    """Generate a comprehensive search plan from a single query string."""
    queries = []
    sources = ["duckduckgo", "bing"]

    # 1. Base query on each source
    for src in sources:
        queries.append((src, base_query))

    # 2. Synonym variants
    words = base_query.split()
    for i, word in enumerate(words):
        wl = word.lower()
        if wl in QUERY_SYNONYMS:
            for syn in QUERY_SYNONYMS[wl][:3]:  # top 3 synonyms
                variant = " ".join(words[:i] + [syn] + words[i+1:])
                queries.append(("duckduckgo", variant))

    # 3. State-specific queries (all 50 states)
    # strip "USA"/"US"/"United States" from base, append state
    base_no_country = re.sub(r'\b(USA|US|United States|America)\b', '', base_query, flags=re.IGNORECASE).strip()
    base_no_country = re.sub(r'\s+', ' ', base_no_country)
    for state in US_STATES:
        queries.append(("duckduckgo", f"{base_no_country} {state}"))

    # 4. Region-based queries
    for region in US_REGIONS:
        queries.append(("bing", f"{base_no_country} {region}"))

    return queries

def cmd_run(args):
    requests, BeautifulSoup = _require_deps()

    base_query = args.query
    per_query = 50  # max per query
    start_time = time.time()

    print(f"{'═'*60}")
    print(f"  RUN: \"{base_query}\"")
    print(f"  Auto search → discover → email")
    print(f"{'═'*60}\n")

    # ── Step 1: Build search plan ──
    plan = _build_search_plan(base_query)
    print(f"📋 Search plan: {len(plan)} queries across DuckDuckGo + Bing\n")

    # ── Step 2: Execute search plan ──
    all_results = []
    seen_domains = set()
    query_count = 0

    for source, query in plan:
        query_count += 1
        search_args = argparse.Namespace(
            query=query, limit=per_query, source=source,
            industry=None, region=None, topic=None,
        )

        prefix = f"[{query_count}/{len(plan)}]"

        if source == "duckduckgo":
            batch = _search_duckduckgo(requests, BeautifulSoup, search_args)
        elif source == "bing":
            batch = _search_bing(requests, BeautifulSoup, search_args)
        else:
            continue

        # dedupe within this run
        new_in_batch = 0
        for r in batch:
            domain = r.get("website","").lower()
            if domain and domain not in seen_domains:
                seen_domains.add(domain)
                all_results.append(r)
                new_in_batch += 1

        print(f"  {prefix} {source}: \"{query[:60]}\" → {len(batch)} raw, {new_in_batch} new")

        time.sleep(1.5)  # rate limit between queries

        # progress update every 10 queries
        if query_count % 10 == 0:
            elapsed = time.time() - start_time
            print(f"\n  ── Progress: {query_count}/{len(plan)} queries, "
                  f"{len(all_results)} unique companies, "
                  f"{elapsed:.0f}s elapsed ──\n")

    # ── Step 3: Save companies ──
    print(f"\n{'─'*60}")
    print(f"📊 Search complete: {len(all_results)} unique companies from {query_count} queries")

    existing = read_csv(COMPANIES)
    existing_keys = {normalize_name(r["name"]): i for i, r in enumerate(existing)}
    added = sum(1 for r in all_results if _upsert_company(existing, existing_keys, r))
    write_csv(COMPANIES, existing, COMPANY_FIELDS)
    update_timestamp("companies")
    print(f"✓ Companies: +{added} new, {len(existing)} total\n")

    # ── Step 4: Discover executives ──
    print(f"{'─'*60}")
    print(f"🔍 Discovering executives from company websites...\n")
    discover_args = argparse.Namespace(company=None)
    cmd_discover(discover_args)

    # ── Step 5: Generate emails ──
    print(f"\n{'─'*60}")
    print(f"📧 Generating emails...\n")
    email_args = argparse.Namespace(pattern=None, company=None)
    cmd_email(email_args)

    # ── Final status ──
    elapsed = time.time() - start_time
    print(f"\n{'═'*60}")
    print(f"  DONE in {elapsed:.0f}s")
    print(f"{'═'*60}\n")
    cmd_status(argparse.Namespace())


# ══════════════════════════════════════════════════════════════════════════════
# refresh — 保留旧接口（调用 run）
# ══════════════════════════════════════════════════════════════════════════════

def cmd_refresh(args):
    if args.query:
        cmd_run(args)
    else:
        print("Error: --query required. Example:")
        print('  python3 refresh.py refresh --query "Trimble reseller dealer USA"')
        print("\nOr use 'run' directly:")
        print('  python3 refresh.py run "Trimble reseller dealer USA"')


# ══════════════════════════════════════════════════════════════════════════════
# status — 数据集状态
# ══════════════════════════════════════════════════════════════════════════════

def cmd_status(args):
    companies  = read_csv(COMPANIES)
    executives = read_csv(EXECUTIVES)
    timestamps = {}
    if os.path.exists(UPDATED_FILE):
        with open(UPDATED_FILE) as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    timestamps[k] = v

    print("═══ Data Status ═══\n")

    print(f"📁 companies.csv: {len(companies)} records")
    if companies:
        brands = {}
        for r in companies:
            b = r.get("brand","") or "—"
            brands[b] = brands.get(b, 0) + 1
        print(f"   Brands:  {', '.join(f'{k}: {v}' for k,v in sorted(brands.items()))}")
    print(f"   Updated: {timestamps.get('companies', 'never')}\n")

    print(f"📁 executives.csv: {len(executives)} records")
    if executives:
        levels = {}
        for r in executives:
            l = r.get("role_level","") or "?"
            levels[l] = levels.get(l, 0) + 1
        has_email = sum(1 for r in executives if r.get("email_work","").strip())
        has_phone = sum(1 for r in executives if r.get("phone","").strip())
        has_li    = sum(1 for r in executives if r.get("linkedin_url","").strip())
        n = len(executives)
        print(f"   Levels:  {', '.join(f'{k}: {v}' for k,v in sorted(levels.items()))}")
        print(f"   Email:   {has_email}/{n} ({100*has_email//n}%)")
        print(f"   Phone:   {has_phone}/{n} ({100*has_phone//n}%)")
        print(f"   LinkedIn:{has_li}/{n} ({100*has_li//n}%)")
    print(f"   Updated: {timestamps.get('executives', 'never')}")

    # recommendations
    print("\n── Recommendations ──")
    if executives:
        no_email = len(executives) - sum(1 for r in executives if r.get("email_work","").strip())
        low_conf = sum(1 for r in executives if r.get("confidence","") == "low")
        if no_email:
            print(f"  💡 {no_email} missing email → python3 refresh.py email")
        if low_conf:
            print(f"  💡 {low_conf} low-confidence → python3 refresh.py enrich")
    if not companies:
        print("  ⚠️  No companies → python3 refresh.py search --source yc --industry <topic>")


# ══════════════════════════════════════════════════════════════════════════════
# GUI launcher — simple double-click interface for macOS/Windows bundles
# ══════════════════════════════════════════════════════════════════════════════

def _run_cli_command(name, func, args):
    buf = io.StringIO()
    try:
        with redirect_stdout(buf), redirect_stderr(buf):
            func(args)
    except SystemExit as e:
        buf.write(f"\nExited with code {e.code}\n")
    except Exception as e:
        buf.write(f"\nError: {e}\n")
    return buf.getvalue()


def launch_gui():
    try:
        import tkinter as tk
        from tkinter import simpledialog, messagebox, scrolledtext
    except Exception as e:
        print(f"GUI unavailable: {e}")
        print("Run from terminal with a command, for example:")
        print('  python3 refresh.py search --query "Trimble reseller dealer USA"')
        return

    root = tk.Tk()
    root.title("Charlie Skill")
    root.geometry("760x520")

    text = scrolledtext.ScrolledText(root, wrap=tk.WORD)
    text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def log(msg):
        text.insert(tk.END, msg)
        text.see(tk.END)

    def ask_query():
        return simpledialog.askstring("Search Company", "Enter search keywords:", parent=root)

    def ask_company():
        return simpledialog.askstring("Company", "Enter company name (optional):", parent=root)

    def run_async(label, runner):
        def worker():
            log(f"\n=== {label} ===\n")
            output = runner()
            log(output + "\n")
        threading.Thread(target=worker, daemon=True).start()

    def search_action():
        query = ask_query()
        if not query:
            return
        limit = simpledialog.askinteger("Limit", "Max results:", parent=root, initialvalue=20, minvalue=1, maxvalue=200) or 20
        args = argparse.Namespace(source="auto", query=query, industry=None, region=None, topic=None, limit=limit)
        run_async("Search", lambda: _run_cli_command("search", cmd_search, args))

    def discover_action():
        company = ask_company()
        args = argparse.Namespace(company=company or None)
        run_async("Discover", lambda: _run_cli_command("discover", cmd_discover, args))

    def email_action():
        company = ask_company()
        args = argparse.Namespace(pattern=None, company=company or None)
        run_async("Email", lambda: _run_cli_command("email", cmd_email, args))

    def enrich_action():
        company = ask_company()
        args = argparse.Namespace(source="all", company=company or None)
        run_async("Enrich", lambda: _run_cli_command("enrich", cmd_enrich, args))

    def status_action():
        args = argparse.Namespace()
        run_async("Status", lambda: _run_cli_command("status", cmd_status, args))

    buttons = tk.Frame(root)
    buttons.pack(fill=tk.X, padx=10, pady=(0, 10))

    tk.Button(buttons, text="Search Company", command=search_action).pack(side=tk.LEFT, padx=4)
    tk.Button(buttons, text="Discover Executives", command=discover_action).pack(side=tk.LEFT, padx=4)
    tk.Button(buttons, text="Generate Emails", command=email_action).pack(side=tk.LEFT, padx=4)
    tk.Button(buttons, text="Enrich Contacts", command=enrich_action).pack(side=tk.LEFT, padx=4)
    tk.Button(buttons, text="Status", command=status_action).pack(side=tk.LEFT, padx=4)
    tk.Button(buttons, text="Quit", command=root.destroy).pack(side=tk.RIGHT, padx=4)

    log(
        "Charlie Skill\n"
        "Use the buttons above to search companies, discover executives, generate emails, enrich contacts, or check status.\n"
        "This launcher is for double-click use in the packaged app.\n"
    )

    root.mainloop()


# ══════════════════════════════════════════════════════════════════════════════
# main
# ══════════════════════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) == 1:
        launch_gui()
        return

    parser = argparse.ArgumentParser(
        description="company-filter-refresh: full dataset refresh tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # search
    ps = sub.add_parser("search", help="Search for companies from public sources")
    ps.add_argument("--source", choices=["auto","duckduckgo","bing","google","yc","awesome"],
                    default="auto", help="Data source (default: auto = try all)")
    ps.add_argument("--query", help="Search query")
    ps.add_argument("--industry", help="Industry filter (for YC)")
    ps.add_argument("--region", help="Region filter (for YC)")
    ps.add_argument("--topic", help="Topic for awesome lists")
    ps.add_argument("--limit", type=int, default=20, help="Max results (default: 20)")

    # discover
    pd = sub.add_parser("discover", help="Discover executives from company websites")
    pd.add_argument("--company", help="Only for a specific company")

    # enrich
    pe = sub.add_parser("enrich", help="Enrich contacts from B2B platforms")
    pe.add_argument("--source", choices=["all","rocketreach","google"], default="all")
    pe.add_argument("--company", help="Only for a specific company")

    # email
    pm = sub.add_parser("email", help="Generate emails from name + domain")
    pm.add_argument("--pattern", help="Email pattern (default: {first}.{last}@{domain})")
    pm.add_argument("--company", help="Only for a specific company")

    # import
    pi = sub.add_parser("import", help="Import from external CSV")
    pi.add_argument("target", choices=["companies","executives"])
    pi.add_argument("--file", required=True, help="Source CSV file")
    pi.add_argument("--mapping", help="Column mapping: dest=src,dest2=src2")

    # merge
    pg = sub.add_parser("merge", help="Merge another CSV into existing data")
    pg.add_argument("target", choices=["companies","executives"])
    pg.add_argument("--file", required=True, help="Source CSV to merge")

    # run (main command)
    prun = sub.add_parser("run", help="One command: search → discover → email (fully automatic)")
    prun.add_argument("query", help='Search query, e.g. "Trimble reseller dealer surveying USA"')

    # refresh (alias for run)
    pr = sub.add_parser("refresh", help="Alias for run")
    pr.add_argument("--query", help="Search query")
    pr.add_argument("--mode", choices=["full","companies","executives","targeted"], default="full")
    pr.add_argument("--industry", help="Industry for targeted mode")
    pr.add_argument("--company", help="Specific company")
    pr.add_argument("--limit", type=int, default=50)

    # status
    sub.add_parser("status", help="Dataset status and recommendations")

    args = parser.parse_args()
    {
        "run":      cmd_run,
        "search":   cmd_search,
        "discover": cmd_discover,
        "enrich":   cmd_enrich,
        "email":    cmd_email,
        "import":   cmd_import,
        "merge":    cmd_merge,
        "refresh":  cmd_refresh,
        "status":   cmd_status,
    }[args.command](args)


if __name__ == "__main__":
    main()

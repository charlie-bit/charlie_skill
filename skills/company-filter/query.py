#!/usr/bin/env python3
"""
company-filter query tool
离线查询 companies.csv / executives.csv / exclusions.csv

Usage:
  python query.py companies
  python query.py companies --brand Trimble
  python query.py companies --region TX

  python query.py executives
  python query.py executives --company "AllTerra Central"
  python query.py executives --role C
  python query.py executives --confidence high
  python query.py executives --email-only

  python query.py all
  python query.py all --brand Leica --role C
  python query.py all --exclude

  python query.py exclusions
  python query.py exclusions --add "Stripe" --reason customer
  python query.py exclusions --add "Plaid" --reason rejected --expires 2026-10-01 --notes "Q4 revisit"
  python query.py exclusions --remove "Stripe"

  # 导出 CSV
  python query.py all --brand Trimble --csv > output.csv
"""

import csv
import sys
import os
import argparse
from datetime import date, datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
COMPANIES_CSV   = os.path.join(DATA_DIR, "companies.csv")
EXECUTIVES_CSV  = os.path.join(DATA_DIR, "executives.csv")
EXCLUSIONS_CSV  = os.path.join(DATA_DIR, "exclusions.csv")


# ── helpers ──────────────────────────────────────────────────────────────────

def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

def col(width, text):
    text = str(text or "")
    if len(text) > width:
        text = text[:width-1] + "…"
    return text.ljust(width)

def print_table(rows, columns):
    """columns: list of (header, field, width)"""
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

def print_csv(rows, columns):
    fields = [f for _, f, _ in columns]
    w = csv.DictWriter(sys.stdout, fieldnames=fields, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)

def excluded_names():
    """Return set of company names currently in exclusions (active, not expired)."""
    rows = read_csv(EXCLUSIONS_CSV)
    today = date.today().isoformat()
    names = set()
    for r in rows:
        exp = r.get("expires_at", "").strip()
        if exp and exp < today:
            continue  # expired
        names.add(r["company_name"].strip().lower())
    return names


# ── subcommands ───────────────────────────────────────────────────────────────

def cmd_companies(args):
    rows = read_csv(COMPANIES_CSV)

    if args.brand:
        rows = [r for r in rows if args.brand.lower() in r.get("brand","").lower()]
    if args.region:
        rows = [r for r in rows if args.region.lower() in r.get("region","").lower()]
    if args.exclude:
        ex = excluded_names()
        rows = [r for r in rows if r["name"].strip().lower() not in ex]

    columns = [
        ("Company",     "name",        28),
        ("Brand",       "brand",        8),
        ("HQ",          "region",      16),
        ("Website",     "website",     28),
        ("Updated",     "updated_at",  12),
    ]
    if args.csv:
        print_csv(rows, columns)
    else:
        print_table(rows, columns)


def cmd_executives(args):
    rows = read_csv(EXECUTIVES_CSV)

    if args.company:
        rows = [r for r in rows if args.company.lower() in r.get("company_name","").lower()]
    if args.brand:
        rows = [r for r in rows if args.brand.lower() in r.get("brand","").lower()]
    if args.role:
        rows = [r for r in rows if r.get("role_level","").upper() == args.role.upper()]
    if args.confidence:
        rows = [r for r in rows if r.get("confidence","").lower() == args.confidence.lower()]
    if args.email_only:
        rows = [r for r in rows if r.get("email_work","").strip()]
    if args.exclude:
        ex = excluded_names()
        rows = [r for r in rows if r.get("company_name","").strip().lower() not in ex]

    columns = [
        ("Company",      "company_name",   28),
        ("Executive",    "executive_name", 22),
        ("Title",        "title",          22),
        ("Level",        "role_level",      6),
        ("Email",        "email_work",     36),
        ("Phone",        "phone",          16),
        ("Confidence",   "confidence",     10),
    ]
    if args.csv:
        print_csv(rows, columns)
    else:
        print_table(rows, columns)


def cmd_all(args):
    """Join companies + executives into one flat view."""
    companies  = {r["name"]: r for r in read_csv(COMPANIES_CSV)}
    executives = read_csv(EXECUTIVES_CSV)

    rows = []
    for e in executives:
        c = companies.get(e.get("company_name",""), {})
        rows.append({
            "company_name":   e.get("company_name",""),
            "brand":          e.get("brand",""),
            "headquarters":   e.get("headquarters",""),
            "website":        c.get("website",""),
            "executive_name": e.get("executive_name",""),
            "title":          e.get("title",""),
            "role_level":     e.get("role_level",""),
            "linkedin_url":   e.get("linkedin_url",""),
            "email_work":     e.get("email_work",""),
            "phone":          e.get("phone",""),
            "confidence":     e.get("confidence",""),
        })

    if args.brand:
        rows = [r for r in rows if args.brand.lower() in r.get("brand","").lower()]
    if args.region:
        rows = [r for r in rows if args.region.lower() in r.get("headquarters","").lower()]
    if args.role:
        rows = [r for r in rows if r.get("role_level","").upper() == args.role.upper()]
    if args.confidence:
        rows = [r for r in rows if r.get("confidence","").lower() == args.confidence.lower()]
    if args.email_only:
        rows = [r for r in rows if r.get("email_work","").strip()]
    if args.exclude:
        ex = excluded_names()
        rows = [r for r in rows if r.get("company_name","").strip().lower() not in ex]

    columns = [
        ("Company",     "company_name",   24),
        ("Brand",       "brand",           8),
        ("HQ",          "headquarters",   16),
        ("Executive",   "executive_name", 22),
        ("Title",       "title",          22),
        ("Lvl",         "role_level",      4),
        ("Email",       "email_work",     36),
        ("Phone",       "phone",          16),
        ("Conf",        "confidence",      6),
    ]
    if args.csv:
        print_csv(rows, columns)
    else:
        print_table(rows, columns)


def cmd_exclusions(args):
    rows = read_csv(EXCLUSIONS_CSV) if os.path.exists(EXCLUSIONS_CSV) else []
    fieldnames = ["company_name","reason","since","expires_at","notes","added_by","source"]

    # -- add
    if args.add:
        existing = [r["company_name"].lower() for r in rows]
        if args.add.lower() in existing:
            print(f"⚠️  '{args.add}' already in exclusions. Use --remove first to update.")
            return
        rows.append({
            "company_name": args.add,
            "reason":       args.reason or "manual",
            "since":        date.today().isoformat(),
            "expires_at":   args.expires or "",
            "notes":        args.notes or "",
            "added_by":     "user",
            "source":       "manual",
        })
        write_csv(EXCLUSIONS_CSV, rows, fieldnames)
        print(f"✓ Added '{args.add}' to exclusions (reason: {args.reason})")
        return

    # -- remove
    if args.remove:
        before = len(rows)
        rows = [r for r in rows if r["company_name"].lower() != args.remove.lower()]
        if len(rows) < before:
            write_csv(EXCLUSIONS_CSV, rows, fieldnames)
            print(f"✓ Removed '{args.remove}' from exclusions")
        else:
            print(f"⚠️  '{args.remove}' not found in exclusions")
        return

    # -- list
    today = date.today().isoformat()
    active   = [r for r in rows if not r.get("expires_at") or r["expires_at"] >= today]
    expired  = [r for r in rows if r.get("expires_at") and r["expires_at"] < today]

    columns = [
        ("Company",   "company_name", 28),
        ("Reason",    "reason",       12),
        ("Since",     "since",        12),
        ("Expires",   "expires_at",   12),
        ("Notes",     "notes",        30),
    ]

    if args.csv:
        print_csv(active, columns)
        return

    print(f"=== Exclusions ({len(active)} active, {len(expired)} expired) ===\n")

    by_reason = {}
    for r in active:
        by_reason.setdefault(r.get("reason","other"), []).append(r)

    for reason, group in sorted(by_reason.items()):
        print(f"[{reason.upper()}] ({len(group)})")
        print_table(group, columns)
        print()

    if expired:
        print(f"⏰  {len(expired)} expired exclusion(s) — consider re-evaluating:")
        for r in expired:
            print(f"   • {r['company_name']} (expired {r['expires_at']}) — {r.get('notes','')}")


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="company-filter offline query tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # shared flags
    def add_shared(p):
        p.add_argument("--brand",      help="Filter by brand (Trimble / Leica)")
        p.add_argument("--region",     help="Filter by region/state keyword")
        p.add_argument("--role",       help="Filter by role_level: C / VP / D")
        p.add_argument("--confidence", help="Filter by confidence: high / medium / low")
        p.add_argument("--email-only", action="store_true", help="Only show rows with email")
        p.add_argument("--exclude",    action="store_true", help="Apply exclusions.csv filter")
        p.add_argument("--csv",        action="store_true", help="Output as CSV")

    # companies
    pc = sub.add_parser("companies", help="Query companies.csv")
    add_shared(pc)

    # executives
    pe = sub.add_parser("executives", help="Query executives.csv")
    add_shared(pe)
    pe.add_argument("--company", help="Filter by company name (partial match)")

    # all (join)
    pa = sub.add_parser("all", help="Joined view: companies + executives")
    add_shared(pa)
    pa.add_argument("--company", help="Filter by company name (partial match)")

    # exclusions
    px = sub.add_parser("exclusions", help="Manage exclusions.csv")
    px.add_argument("--add",     metavar="COMPANY", help="Add company to exclusions")
    px.add_argument("--reason",  choices=["customer","in_pipeline","rejected","dnd"], help="Exclusion reason")
    px.add_argument("--expires", metavar="YYYY-MM-DD", help="Expiry date (optional)")
    px.add_argument("--notes",   help="Notes / context")
    px.add_argument("--remove",  metavar="COMPANY", help="Remove company from exclusions")
    px.add_argument("--csv",     action="store_true", help="Output as CSV")

    args = parser.parse_args()

    if args.command == "companies":
        cmd_companies(args)
    elif args.command == "executives":
        cmd_executives(args)
    elif args.command == "all":
        cmd_all(args)
    elif args.command == "exclusions":
        cmd_exclusions(args)


if __name__ == "__main__":
    main()

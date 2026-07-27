#!/usr/bin/env python3
"""
LinkedIn Job Description Scraper for Data Science Roles

Fetches ~100 job listings from LinkedIn's public (no-auth) jobs API,
captures full descriptions and metadata, and writes to a timestamped JSON file.

Usage:
    pip install requests beautifulsoup4 lxml
    python scrape_linkedin_jobs.py

If LinkedIn blocks requests frequently, install playwright and set
USE_PLAYWRIGHT=True below, then run: playwright install chromium
"""

import json
import logging
import random
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SEARCH_ROLES = [
    "Data Scientist",
    "AI Engineer",
    "ML Engineer",
    "MLOps Engineer",
    "Machine Learning Engineer",
    "Applied Scientist",
    "Data Science",
]

TARGET_TOTAL = 100
LOCATION = "United States"

# Seconds to wait between detail fetches (randomised ± 50%)
BASE_DELAY = 2.5
# Seconds to wait between role switches
ROLE_SWITCH_DELAY = (6, 12)

BASE_URL = "https://www.linkedin.com"
SEARCH_API = f"{BASE_URL}/jobs-guest/jobs/api/seeMoreJobPostings/search"
DETAIL_API = f"{BASE_URL}/jobs-guest/jobs/api/jobPosting"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.linkedin.com/jobs/",
    "Connection": "keep-alive",
}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sleep(seconds: float) -> None:
    jitter = seconds * random.uniform(0.5, 1.5)
    time.sleep(jitter)


def _text(tag) -> str:
    return tag.get_text(separator=" ", strip=True) if tag else ""


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_job_card(card: BeautifulSoup) -> Optional[dict]:
    """Extract lightweight metadata from a search-result card."""
    try:
        # job_id from data-entity-urn or href
        job_id = None
        urn = card.get("data-entity-urn", "")
        if urn:
            job_id = urn.rsplit(":", 1)[-1]
        if not job_id:
            link = card.find("a", href=re.compile(r"/jobs/view/\d+"))
            if link:
                m = re.search(r"/jobs/view/(\d+)", link["href"])
                job_id = m.group(1) if m else None
        if not job_id:
            return None

        title_tag = card.find(
            ["h3", "h4"],
            class_=re.compile(r"base-search-card__title|job-search-card__title"),
        )
        company_tag = card.find(
            class_=re.compile(r"base-search-card__subtitle|job-search-card__company-name")
        )
        location_tag = card.find(class_=re.compile(r"job-search-card__location"))
        time_tag = card.find("time")

        return {
            "job_id": job_id,
            "url": f"{BASE_URL}/jobs/view/{job_id}/",
            "title": _text(title_tag),
            "company": _text(company_tag),
            "location": _text(location_tag),
            "posted_date": time_tag.get("datetime", "") if time_tag else "",
            "posted_text": _text(time_tag),
        }
    except Exception as exc:
        log.debug("Card parse error: %s", exc)
        return None


def parse_job_detail(html: str) -> dict:
    """Extract full description and structured criteria from the detail page."""
    soup = BeautifulSoup(html, "lxml")

    # Description — LinkedIn wraps it in show-more-less-html__markup
    desc_div = soup.find("div", class_=re.compile(r"show-more-less-html__markup"))
    if not desc_div:
        desc_div = soup.find("div", class_=re.compile(r"description__text"))
    description = desc_div.get_text(separator="\n", strip=True) if desc_div else ""

    # Criteria list (Seniority, Employment type, Job function, Industries)
    criteria: dict[str, str] = {
        "seniority_level": "",
        "employment_type": "",
        "job_function": "",
        "industries": "",
    }
    crit_list = soup.find("ul", class_=re.compile(r"description__job-criteria-list"))
    if crit_list:
        for item in crit_list.find_all("li"):
            header = _text(item.find("h3")).lower()
            value = _text(item.find("span"))
            if "seniority" in header:
                criteria["seniority_level"] = value
            elif "employment" in header:
                criteria["employment_type"] = value
            elif "function" in header:
                criteria["job_function"] = value
            elif "industr" in header:
                criteria["industries"] = value

    # Applicant count (shown as "X applicants" or "Over X applicants")
    applicants_tag = soup.find(
        class_=re.compile(r"num-applicants__caption|applicant-count|tvm__text")
    )
    applicants = _text(applicants_tag)

    # Company size / industry from the top section (sometimes present)
    company_size = ""
    company_industry = ""
    company_meta = soup.find("div", class_=re.compile(r"job-details-jobs-unified-top-card"))
    if company_meta:
        spans = company_meta.find_all("span")
        texts = [_text(s) for s in spans if _text(s)]
        # Heuristic: look for "employees" and common industry keywords
        for t in texts:
            if "employee" in t.lower():
                company_size = t
            if any(
                k in t.lower()
                for k in ["technology", "software", "healthcare", "finance", "consulting"]
            ):
                company_industry = t

    # Remote / hybrid / on-site badge
    work_type = ""
    badge = soup.find(class_=re.compile(r"workplace-type|work-arrangement"))
    if badge:
        work_type = _text(badge)
    else:
        # Fallback: search for common terms in the top-card text
        topcard = soup.find("div", class_=re.compile(r"top-card|unified-top-card"))
        if topcard:
            tc_text = _text(topcard).lower()
            for term in ("remote", "hybrid", "on-site", "onsite"):
                if term in tc_text:
                    work_type = term.capitalize()
                    break

    return {
        "description": description,
        "description_word_count": len(description.split()),
        "applicants": applicants,
        "company_size": company_size,
        "company_industry": company_industry,
        "work_arrangement": work_type,
        **criteria,
    }


# ---------------------------------------------------------------------------
# Network
# ---------------------------------------------------------------------------

def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


def fetch_listings(
    session: requests.Session, keyword: str, start: int, location: str = LOCATION
) -> list[dict]:
    """Fetch one page (~25 cards) of search results."""
    try:
        resp = session.get(
            SEARCH_API,
            params={
                "keywords": keyword,
                "location": location,
                "start": start,
                "f_JT": "F",   # Full-time
                "sortBy": "R", # Most recent
            },
            timeout=20,
        )
        if resp.status_code == 429:
            log.warning("Rate-limited (429). Sleeping 60 s …")
            time.sleep(60)
            return []
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")
        cards = []
        for li in soup.find_all("li"):
            div = li.find("div", class_=re.compile(r"base-card|job-search-card"))
            if div:
                job = parse_job_card(div)
                if job:
                    cards.append(job)

        log.info("  Listings fetched: %d  (start=%d, keyword='%s')", len(cards), start, keyword)
        return cards

    except requests.RequestException as exc:
        log.error("Listings request failed: %s", exc)
        return []


def fetch_detail(session: requests.Session, job_id: str) -> dict:
    """Fetch the detail page for one job."""
    _sleep(BASE_DELAY)
    try:
        resp = session.get(f"{DETAIL_API}/{job_id}", timeout=20)
        if resp.status_code == 429:
            log.warning("Rate-limited on detail fetch. Sleeping 90 s …")
            time.sleep(90)
            return {}
        resp.raise_for_status()
        return parse_job_detail(resp.text)
    except requests.RequestException as exc:
        log.error("Detail fetch failed for job %s: %s", job_id, exc)
        return {}


# ---------------------------------------------------------------------------
# Main scraping loop
# ---------------------------------------------------------------------------

def scrape(target: int = TARGET_TOTAL) -> list[dict]:
    session = make_session()
    all_jobs: list[dict] = []
    seen_ids: set[str] = set()

    jobs_per_role = max(10, (target // len(SEARCH_ROLES)) + 3)

    for role in SEARCH_ROLES:
        if len(all_jobs) >= target:
            break

        log.info("\n=== Role: '%s' (target %d per role) ===", role, jobs_per_role)
        role_collected = 0
        start = 0

        while role_collected < jobs_per_role and len(all_jobs) < target:
            listings = fetch_listings(session, role, start)
            if not listings:
                break

            for card in listings:
                if role_collected >= jobs_per_role or len(all_jobs) >= target:
                    break
                jid = card["job_id"]
                if jid in seen_ids:
                    continue
                seen_ids.add(jid)

                log.info("  [%3d/%d] %s @ %s", len(all_jobs) + 1, target, card["title"], card["company"])
                detail = fetch_detail(session, jid)

                full_record: dict = {
                    # --- identifiers ---
                    "job_id": jid,
                    "url": card["url"],
                    # --- card fields ---
                    "title": card["title"],
                    "company": card["company"],
                    "location": card["location"],
                    "posted_date": card["posted_date"],
                    "posted_text": card["posted_text"],
                    # --- detail fields ---
                    "description": detail.get("description", ""),
                    "description_word_count": detail.get("description_word_count", 0),
                    "seniority_level": detail.get("seniority_level", ""),
                    "employment_type": detail.get("employment_type", ""),
                    "job_function": detail.get("job_function", ""),
                    "industries": detail.get("industries", ""),
                    "work_arrangement": detail.get("work_arrangement", ""),
                    "company_size": detail.get("company_size", ""),
                    "company_industry": detail.get("company_industry", ""),
                    "applicants": detail.get("applicants", ""),
                    # --- provenance ---
                    "search_keyword": role,
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                }

                all_jobs.append(full_record)
                role_collected += 1

            start += len(listings)
            if start > 200:  # LinkedIn caps public results at ~200 per search
                break
            _sleep(BASE_DELAY)

        log.info("  '%s' done — collected %d jobs", role, role_collected)
        if len(all_jobs) < target:
            wait = random.uniform(*ROLE_SWITCH_DELAY)
            log.info("  Waiting %.1f s before next role …", wait)
            time.sleep(wait)

    return all_jobs[:target]


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def save(jobs: list[dict], out_dir: Path = Path(".")) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_file = out_dir / f"linkedin_ds_jobs_{ts}.json"

    payload = {
        "metadata": {
            "description": "LinkedIn job postings for data science roles",
            "source": "LinkedIn public jobs API (no auth)",
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "total_jobs": len(jobs),
            "target_roles": SEARCH_ROLES,
            "location_filter": LOCATION,
            "schema_version": "1.0",
            "fields": [
                "job_id", "url", "title", "company", "location",
                "posted_date", "posted_text", "description",
                "description_word_count", "seniority_level",
                "employment_type", "job_function", "industries",
                "work_arrangement", "company_size", "company_industry",
                "applicants", "search_keyword", "scraped_at",
            ],
        },
        "jobs": jobs,
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    log.info("Saved %d jobs → %s", len(jobs), out_file)
    return out_file


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    log.info("LinkedIn data-science job scraper starting …")
    log.info("Target: %d jobs | Roles: %s", TARGET_TOTAL, ", ".join(SEARCH_ROLES))

    jobs = scrape(TARGET_TOTAL)

    if not jobs:
        log.error(
            "No jobs collected. LinkedIn may be rate-limiting or blocking.\n"
            "  Options:\n"
            "  1. Wait ~30 min and retry.\n"
            "  2. Use a VPN or residential proxy.\n"
            "  3. Switch to the Playwright browser-automation approach (see README).\n"
            "  4. Use the official LinkedIn Jobs API if you have API access."
        )
    else:
        out = save(jobs)
        print(f"\n✓  {len(jobs)} jobs saved to: {out}")

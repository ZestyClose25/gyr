import time
import requests
from bs4 import BeautifulSoup

import config

SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
JOB_VIEW_URL = "https://www.linkedin.com/jobs/view/{job_id}"

HEADERS = {"User-Agent": config.USER_AGENT}


def _get_with_retry(url, params=None):
    for attempt in range(1, config.MAX_RETRIES + 1):
        try:
            resp = requests.get(
                url, params=params, headers=HEADERS, timeout=config.REQUEST_TIMEOUT
            )
            if resp.status_code == 200:
                return resp
            print(f"  [warn] {url} -> HTTP {resp.status_code} (attempt {attempt})")
        except requests.exceptions.RequestException as e:
            print(f"  [warn] request failed: {e} (attempt {attempt})")
        time.sleep(config.REQUEST_DELAY_SECONDS * attempt)
    return None


def _extract_job_id(card):
    urn = card.get("data-entity-urn", "")
    # format: urn:li:jobPosting:1234567890
    if ":" in urn:
        return urn.split(":")[-1]
    return None


def search_jobs(keyword, start=0):
    """
    Fetch one page (~25 results) of job cards for a keyword, filtered to
    postings within TIME_WINDOW_HOURS. Returns a list of dicts.
    """
    params = {
        "keywords": keyword,
        "location": config.LOCATION,
        "f_TPR": f"r{config.TIME_WINDOW_SECONDS}",
        "start": start,
    }
    resp = _get_with_retry(SEARCH_URL, params=params)
    time.sleep(config.REQUEST_DELAY_SECONDS)
    if resp is None:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    cards = soup.select("li div.base-card")
    results = []

    for card in cards:
        job_id = _extract_job_id(card)
        if not job_id:
            continue

        title_el = card.select_one("h3.base-search-card__title")
        company_el = card.select_one("h4.base-search-card__subtitle a")
        location_el = card.select_one("span.job-search-card__location")
        time_el = card.select_one("time.job-search-card__listdate, time")
        link_el = card.select_one("a.base-card__full-link")

        results.append({
            "job_id": job_id,
            "title": title_el.get_text(strip=True) if title_el else "Unknown title",
            "company": company_el.get_text(strip=True) if company_el else "Unknown company",
            "location": location_el.get_text(strip=True) if location_el else config.LOCATION,
            "posted": time_el.get_text(strip=True) if time_el else "",
            "posted_datetime": time_el.get("datetime") if time_el else "",
            "job_url": link_el.get("href", "").split("?")[0] if link_el else JOB_VIEW_URL.format(job_id=job_id),
        })

    return results


def collect_pool_raw(keywords, raw_limit):
    seen = {}
    for keyword in keywords:
        if len(seen) >= raw_limit:
            break
        start = 0
        while len(seen) < raw_limit:
            batch = search_jobs(keyword, start=start)
            if not batch:
                break
            for job in batch:
                if job["job_id"] not in seen:
                    seen[job["job_id"]] = job
            if len(batch) < 25:
                break  # last page for this keyword
            start += 25
    return list(seen.values())[:raw_limit]


def _extract_apply_type(html):
    if "Easy Apply" in html:
        return "Easy Apply"
    if "apply-link-offsite" in html or "OFFSITE_APPLY" in html or "offsiteApply" in html:
        return "External"
    if "jobs-apply-button" in html:
        return "External"
    return "Unknown"


def _extract_description(soup):
    desc_el = soup.select_one("div.show-more-less-html__markup")
    if not desc_el:
        return ""
    text = desc_el.get_text(separator=" ", strip=True)
    text = " ".join(text.split())  # collapse extra whitespace
    if len(text) > config.DESCRIPTION_MAX_CHARS:
        text = text[: config.DESCRIPTION_MAX_CHARS].rstrip() + "..."
    return text


def get_job_detail(job_id):
    resp = _get_with_retry(JOB_VIEW_URL.format(job_id=job_id))
    time.sleep(config.REQUEST_DELAY_SECONDS)
    if resp is None:
        return {"apply_type": "Unknown", "description": ""}

    soup = BeautifulSoup(resp.text, "html.parser")
    return {
        "apply_type": _extract_apply_type(resp.text),
        "description": _extract_description(soup),
    }

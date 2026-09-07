import os
from datetime import datetime
from zoneinfo import ZoneInfo

from joblib import Parallel, delayed

import config
import linkedin_scraper as li
import sheets_writer as sheets

IST = ZoneInfo("Asia/Kolkata")


def _sort_key(job):
    return job.get("posted_datetime") or ""


def rank_pool(pool_name, raw_jobs, existing_ids):
    fresh = [j for j in raw_jobs if j["job_id"] not in existing_ids]
    fresh.sort(key=_sort_key, reverse=True)

    candidates = fresh[: config.DETAIL_CHECK_TOP_N]
    rest = fresh[config.DETAIL_CHECK_TOP_N :]

    if candidates:
        print(f"  Fetching details for {len(candidates)} candidates...")
        details = Parallel(n_jobs=4, backend="threading")(
            delayed(li.get_job_detail)(j["job_id"]) for j in candidates
        )
        for job, detail in zip(candidates, details):
            job["apply_type"] = detail["apply_type"]
            job["description"] = detail["description"]

    if config.PRIORITIZE_EXTERNAL_APPLY and candidates:
        external = [j for j in candidates if j["apply_type"] == "External"]
        others = [j for j in candidates if j["apply_type"] != "External"]
        ranked = external + others + rest
    else:
        ranked = candidates + rest

    final = ranked[: config.FINAL_PER_POOL]

    missing = [j for j in final if "description" not in j]
    if missing:
        print(f"  Backfilling details for {len(missing)} additional picks...")
        details = Parallel(n_jobs=4, backend="threading")(
            delayed(li.get_job_detail)(j["job_id"]) for j in missing
        )
        for job, detail in zip(missing, details):
            job["apply_type"] = detail["apply_type"]
            job["description"] = detail["description"]

    return final


def main():
    credentials_path = os.environ.get("GCP_CREDENTIALS_PATH", "credentials.json")
    sheet_id = os.environ.get("GOOGLE_SHEET_ID")
    if not sheet_id:
        raise SystemExit("GOOGLE_SHEET_ID environment variable is not set.")

    existing_ids = sheets.get_existing_job_ids(credentials_path, sheet_id)
    print(f"{len(existing_ids)} job IDs already in the sheet.")

    today_ist = datetime.now(IST).strftime("%Y-%m-%d %H:%M")
    final_rows = []

    for pool_name, keywords in config.POOLS.items():
        print(f"\n== Pool: {pool_name} ==")
        raw = li.collect_pool_raw(keywords, config.RAW_PER_POOL)
        print(f"  Collected {len(raw)} raw postings within {config.TIME_WINDOW_HOURS}h.")

        top = rank_pool(pool_name, raw, existing_ids)
        print(f"  Selected {len(top)} for the sheet.")

        for job in top:
            final_rows.append({
                "date_added": today_ist,
                "pool": pool_name,
                "title": job["title"],
                "company": job["company"],
                "location": job["location"],
                "posted": job["posted"],
                "description": job.get("description", ""),
                "apply_type": job.get("apply_type", "Unknown"),
                "job_url": job["job_url"],
                "job_id": job["job_id"],
            })

    sheets.append_jobs(credentials_path, sheet_id, final_rows)
    print(f"\nDone. {len(final_rows)} new internships added.")


if __name__ == "__main__":
    main()

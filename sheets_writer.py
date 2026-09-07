import os
import gspread
import config


def _connect(credentials_path, sheet_id):
    gc = gspread.service_account(filename=credentials_path)
    sh = gc.open_by_key(sheet_id)
    try:
        ws = sh.worksheet(config.SHEET_TAB_NAME)
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title=config.SHEET_TAB_NAME, rows=1000, cols=len(config.SHEET_HEADERS))
        ws.append_row(config.SHEET_HEADERS)

    # Make sure headers exist even on a pre-existing but empty tab.
    if ws.row_count == 0 or not ws.get_all_values():
        ws.append_row(config.SHEET_HEADERS)

    return ws


def get_existing_job_ids(credentials_path, sheet_id):
    ws = _connect(credentials_path, sheet_id)
    values = ws.get_all_values()
    if len(values) <= 1:
        return set()
    header = values[0]
    try:
        id_col = header.index("Job ID")
    except ValueError:
        return set()
    return {row[id_col] for row in values[1:] if len(row) > id_col and row[id_col]}


def append_jobs(credentials_path, sheet_id, rows):
    if not rows:
        print("Nothing new to append.")
        return

    ws = _connect(credentials_path, sheet_id)
    table_rows = [
        [
            r["date_added"], r["pool"], r["title"], r["company"],
            r["location"], r["posted"], r["description"], r["apply_type"],
            r["job_url"], r["job_id"],
        ]
        for r in rows
    ]
    ws.append_rows(table_rows, value_input_option="USER_ENTERED")
    print(f"Appended {len(table_rows)} rows to '{config.SHEET_TAB_NAME}'.")

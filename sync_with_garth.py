# sync_with_garth.py
import os, json, requests, garth

# --- Env ---
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DB_ID = os.getenv("NOTION_DB_ID")
FETCH_LIMIT  = int(os.getenv("GARMIN_ACTIVITIES_FETCH_LIMIT", "50"))
GARTH_HOME   = os.getenv("GARTH_HOME", "~/.garth")

# --- Notion columns (edit if your names differ) ---
PROP = {
    "name": "Name",
    "date": "Date",
    "garmin_id": "Garmin ID",
    "type": "Type",
    "distance_km": "Distance (km)",
    "duration_s": "Duration (s)",
    "avg_hr": "Avg HR",
}

NOTION_VERSION = "2022-06-28"

def _headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

def _query_by_garmin_id(db_id: str, garmin_id: str):
    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    payload = {
"filter": {"property": PROP["garmin_id"], "rich_text": {"contains": str(garmin_id)}}
        "page_size": 1
    }
    r = requests.post(url, headers=_headers(), data=json.dumps(payload), timeout=60)
    r.raise_for_status()
    res = r.json().get("results", [])
    return res[0]["id"] if res else None

def _create(db_id: str, props: dict):
    url = "https://api.notion.com/v1/pages"
    payload = {"parent": {"database_id": db_id}, "properties": props}
    r = requests.post(url, headers=_headers(), data=json.dumps(payload), timeout=60)
    r.raise_for_status()
    return r.json()["id"]

def _update(page_id: str, props: dict):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {"properties": props}
    r = requests.patch(url, headers=_headers(), data=json.dumps(payload), timeout=60)
    r.raise_for_status()
    return r.json()["id"]

def _props(a: dict):
    aid = a.get("activityId")
    name = a.get("activityName") or (a.get("activityType", {}) or {}).get("typeKey") or "Activity"
    type_key = (a.get("activityType", {}) or {}).get("typeKey")
    start_local = a.get("startTimeLocal") or a.get("startTimeGMT")
    dist_m = a.get("distance") or 0
    dur_s = int(a.get("duration") or 0)
    avg_hr = a.get("averageHR")
    return {
        PROP["name"]:       {"title": [{"text": {"content": name}}]},
        PROP["garmin_id"]:  {"rich_text": [{"text": {"content": str(aid)}}]},
        PROP["date"]:       {"date": {"start": start_local}},
        PROP["type"]:       {"select": {"name": type_key}} if type_key else {"rich_text": [{"text": {"content": ""}}]},
        PROP["distance_km"]:{ "number": round(dist_m/1000.0, 3)},
        PROP["duration_s"]: { "number": dur_s},
        PROP["avg_hr"]:     { "number": avg_hr if avg_hr is not None else None},
    }

def _fetch(limit: int):
    path = "/activitylist-service/activities/search/activities"
    params = {"start": 0, "limit": limit}
    return garth.connectapi(path, params=params)

def main():
    if not NOTION_TOKEN or not NOTION_DB_ID:
        raise SystemExit("NOTION_TOKEN or NOTION_DB_ID not set")
    garth.resume(GARTH_HOME)   # load oauth1/2 from GARTH_HOME
    _ = garth.client.username  # optional ping to confirm auth

    acts = _fetch(FETCH_LIMIT) or []
    print(f"Fetched {len(acts)} activities")

    created = updated = 0
    for a in acts:
        aid = a.get("activityId")
        if not aid:
            continue
        props = _props(a)
        page_id = _query_by_garmin_id(NOTION_DB_ID, str(aid))
        if page_id:
            _update(page_id, props); updated += 1
        else:
            _create(NOTION_DB_ID, props); created += 1

    print(f"Done. Created: {created}, Updated: {updated}")

if __name__ == "__main__":
    main()

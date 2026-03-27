#!/usr/bin/env python3
"""
WBR Data Store - Persists WBR review data for dashboard visualisation.

Saves weekly WBR snapshots to a JSON file so they can be loaded
by a dashboard to show trends, comparisons, and historical data.
"""

import json
import os
from datetime import datetime

# Store data alongside the other bot files
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
WBR_HISTORY_FILE = os.path.join(DATA_DIR, "wbr_history.json")


def load_history():
    """Load the full WBR history from disk."""
    if not os.path.exists(WBR_HISTORY_FILE):
        return {"reviews": [], "last_updated": None}
    try:
        with open(WBR_HISTORY_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"reviews": [], "last_updated": None}


def save_history(history):
    """Write the WBR history back to disk."""
    history["last_updated"] = datetime.now().isoformat()
    with open(WBR_HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def save_wbr_snapshot(wbr_data):
    """
    Save a single WBR week snapshot.

    Args:
        wbr_data: dict returned by get_wbr_data() from wbr_enhanced.py
                  Expected keys: week, created_auto_data, due_done, new_kpis, planning

    Returns:
        True if saved, False on error
    """
    if not wbr_data or not wbr_data.get("week"):
        return False

    history = load_history()

    # Build a flat, dashboard-friendly record
    cad = wbr_data.get("created_auto_data", {})
    dd = wbr_data.get("due_done", {})
    kpi = wbr_data.get("new_kpis", {})
    plan = wbr_data.get("planning", {})

    record = {
        "week": wbr_data["week"],
        "captured_at": datetime.now().isoformat(),

        # Tasks Created / Auto / Data
        "total_tasks": _to_num(cad.get("total_tasks")),
        "auto_tasks": _to_num(cad.get("auto_tasks")),
        "data_tasks": _to_num(cad.get("data_tasks")),

        # Due / Done
        "created": _to_num(dd.get("created")),
        "auto_done": _to_num(dd.get("auto")),
        "data_done": _to_num(dd.get("data")),
        "total_due": _to_num(dd.get("total_due")),
        "total_done": _to_num(dd.get("total_done")),

        # KPIs
        "critical_over_sla": _to_num(kpi.get("critical_over_sla")),
        "returned": _to_num(kpi.get("returned")),
        "repeating": kpi.get("repeating", "-"),
        "new_launches": kpi.get("new_launches", "-"),

        # Planning (hours)
        "created_est_hrs": _to_float(plan.get("created_est")),
        "new_debt_hrs": _to_float(plan.get("new_debt")),
        "planned_hrs": _to_float(plan.get("planned")),
        "debt_hrs": _to_float(plan.get("debt")),

        # Derived metrics for easy dashboard use
        "completion_rate": _completion_rate(dd),
    }

    # Upsert – replace if same week already exists, otherwise append
    existing_idx = next(
        (i for i, r in enumerate(history["reviews"]) if r["week"] == record["week"]),
        None,
    )
    if existing_idx is not None:
        history["reviews"][existing_idx] = record
    else:
        history["reviews"].append(record)

    # Keep sorted by week label (W01, W02, …)
    history["reviews"].sort(key=lambda r: r["week"])

    save_history(history)
    return True


def save_wbr_comparison(current_data, previous_data):
    """
    Save both weeks when a /wbr-compare is run.
    Ensures both snapshots are stored for the dashboard.
    """
    saved_current = save_wbr_snapshot(current_data)
    saved_previous = save_wbr_snapshot(previous_data)
    return saved_current or saved_previous


def get_all_reviews():
    """Return all stored WBR reviews (sorted by week)."""
    history = load_history()
    return history.get("reviews", [])


def get_review_by_week(week_label):
    """Return a single week's review by its label, e.g. 'W07'."""
    for review in get_all_reviews():
        if review["week"] == week_label:
            return review
    return None


def get_latest_n_reviews(n=8):
    """Return the most recent N reviews for trend display."""
    reviews = get_all_reviews()
    return reviews[-n:] if len(reviews) > n else reviews


def get_dashboard_data():
    """
    Return data pre-shaped for the dashboard.
    Includes time series arrays for each metric so charting is easy.
    """
    reviews = get_all_reviews()
    if not reviews:
        return {"weeks": [], "series": {}, "latest": None}

    weeks = [r["week"] for r in reviews]

    series = {
        "total_tasks":       [r.get("total_tasks", 0) for r in reviews],
        "total_due":         [r.get("total_due", 0) for r in reviews],
        "total_done":        [r.get("total_done", 0) for r in reviews],
        "completion_rate":   [r.get("completion_rate", 0) for r in reviews],
        "critical_over_sla": [r.get("critical_over_sla", 0) for r in reviews],
        "returned":          [r.get("returned", 0) for r in reviews],
        "debt_hrs":          [r.get("debt_hrs", 0) for r in reviews],
        "planned_hrs":       [r.get("planned_hrs", 0) for r in reviews],
    }

    return {
        "weeks": weeks,
        "series": series,
        "latest": reviews[-1],
        "total_weeks": len(reviews),
    }


# ── helpers ──────────────────────────────────────────────────────────

def _to_num(val):
    """Convert a string value to int, defaulting to 0."""
    try:
        return int(val) if val and val != "-" else 0
    except (ValueError, TypeError):
        return 0


def _to_float(val):
    """Convert a string value to float, defaulting to 0.0."""
    try:
        return float(val) if val and val != "-" else 0.0
    except (ValueError, TypeError):
        return 0.0


def _completion_rate(due_done):
    """Calculate completion rate from due/done dict."""
    due = _to_num(due_done.get("total_due"))
    done = _to_num(due_done.get("total_done"))
    if due == 0:
        return 0.0
    return round((done / due) * 100, 1)


# ── CLI for manual testing ──────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "dump":
        # Dump current stored data
        data = get_dashboard_data()
        print(json.dumps(data, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "capture":
        # Capture current WBR from Google Sheets and store it
        from wbr_enhanced import get_wbr_data
        wbr = get_wbr_data(week_offset=0)
        if wbr:
            save_wbr_snapshot(wbr)
            print(f"✅ Saved snapshot for {wbr['week']}")

            # Also capture previous week
            prev = get_wbr_data(week_offset=1)
            if prev:
                save_wbr_snapshot(prev)
                print(f"✅ Saved snapshot for {prev['week']}")
        else:
            print("❌ Could not fetch WBR data")
    else:
        print("Usage:")
        print("  python wbr_data_store.py dump      — show stored dashboard data")
        print("  python wbr_data_store.py capture   — fetch & store current + previous week")

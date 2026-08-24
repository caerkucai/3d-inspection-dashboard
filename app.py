import csv
import os
from collections import defaultdict
from datetime import datetime

from flask import Flask, jsonify, render_template

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "data", "CF_Template_Latest.csv")

# ============================================================
# VDO.NINJA STREAM IDS
# ============================================================
ROBOT_STREAM_ID = os.environ.get(
    "ROBOT_STREAM_ID",
    "uthehrobotcam2026"
)

SOFTWARE_STREAM_ID = os.environ.get(
    "SOFTWARE_STREAM_ID",
    "uthehcreaform2026"
)


def make_view_url(stream_id: str) -> str:
    """
    Creates the VDO.Ninja viewer URL used by the dashboard.
    """
    return (
        f"https://vdo.ninja/?view={stream_id}"
        f"&autoplay"
        f"&cleanoutput"
        f"&cleanviewer"
        f"&noaudio"
        f"&codec=h264"
    )


# ============================================================
# CSV FUNCTIONS
# ============================================================

def find_measurement_header(rows):
    """
    Finds the Creaform measurement table header.

    Expected columns include:
    Part, Name, ..., Status
    """
    for index, row in enumerate(rows):
        if (
            len(row) >= 11
            and row[0].strip() == "Part"
            and row[1].strip() == "Name"
            and row[10].strip() == "Status"
        ):
            return index

    return None


def load_csv_results():
    """
    Reads the Creaform CSV and calculates the overall result
    for every inspected part.

    Rules:
        - If any measurement is Failed -> NG
        - Otherwise, if measurements are Passed -> PASS
    """

    empty_result = {
        "parts": [],
        "summary": {
            "pass": 0,
            "ng": 0,
            "total": 0
        },
        "error": None,
        "source_file": os.path.basename(CSV_FILE),
        "updated_at": None
    }

    if not os.path.exists(CSV_FILE):
        empty_result["error"] = "CSV file not found."
        return empty_result

    try:
        with open(
            CSV_FILE,
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as file:
            rows = list(csv.reader(file))

    except (OSError, csv.Error) as exc:
        empty_result["error"] = str(exc)
        return empty_result

    header_index = find_measurement_header(rows)

    if header_index is None:
        empty_result["error"] = "Measurement header not found."
        return empty_result

    grouped_parts = defaultdict(list)

    for row in rows[header_index + 1:]:

        if len(row) < 11:
            continue

        part_name = row[0].strip()

        if not part_name:
            continue

        raw_status = row[10].strip().lower()

        if raw_status == "passed":
            status = "PASS"

        elif raw_status == "failed":
            status = "NG"

        else:
            status = ""

        measurement = {
            "name": row[1].strip(),
            "type": row[2].strip(),
            "dimension": row[4].strip(),
            "tolerance": row[5].strip(),
            "nominal": row[6].strip(),
            "measured": row[7].strip(),
            "deviation": row[8].strip(),
            "out_of_tolerance": row[9].strip(),
            "status_raw": raw_status,
            "status": status
        }

        grouped_parts[part_name].append(measurement)

    parts = []

    for part_name, measurements in grouped_parts.items():

        has_failed = any(
            measurement["status_raw"] == "failed"
            for measurement in measurements
        )

        has_passed = any(
            measurement["status_raw"] == "passed"
            for measurement in measurements
        )

        if has_failed:
            overall_status = "NG"

        elif has_passed:
            overall_status = "PASS"

        else:
            overall_status = "NG"

        failed_count = sum(
            1
            for measurement in measurements
            if measurement["status_raw"] == "failed"
        )

        parts.append({
            "part": part_name,
            "status": overall_status,
            "measurements": measurements,
            "failed_count": failed_count
        })

    pass_count = sum(
        1 for part in parts
        if part["status"] == "PASS"
    )

    ng_count = sum(
        1 for part in parts
        if part["status"] == "NG"
    )

    updated_at = datetime.fromtimestamp(
        os.path.getmtime(CSV_FILE)
    ).strftime("%Y-%m-%d %H:%M:%S")

    return {
        "parts": parts,
        "summary": {
            "pass": pass_count,
            "ng": ng_count,
            "total": len(parts)
        },
        "error": None,
        "source_file": os.path.basename(CSV_FILE),
        "updated_at": updated_at
    }


# ============================================================
# ROUTES
# ============================================================

@app.route("/")
def index():

    return render_template(
        "index.html",

        robot_stream_id=ROBOT_STREAM_ID,

        software_stream_id=SOFTWARE_STREAM_ID,

        robot_view_url=make_view_url(
            ROBOT_STREAM_ID
        ),

        software_view_url=make_view_url(
            SOFTWARE_STREAM_ID
        )
    )


@app.route("/video-test")
def video_test():

    return render_template(
        "video_test.html",

        robot_stream_id=ROBOT_STREAM_ID,

        software_stream_id=SOFTWARE_STREAM_ID,

        robot_view_url=make_view_url(
            ROBOT_STREAM_ID
        ),

        software_view_url=make_view_url(
            SOFTWARE_STREAM_ID
        )
    )


@app.route("/api/inspection-summary")
def inspection_summary():

    return jsonify(
        load_csv_results()
    )


@app.route("/health")
def health():

    return jsonify({
        "ok": True
    })


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
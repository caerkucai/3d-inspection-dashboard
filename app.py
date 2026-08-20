import os
import json
from datetime import datetime
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), 'scan_data.json')
DEFAULT_TOLERANCE = 0.5  # mm


def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"history_count": 0, "history_pass": 0, "latest": None}


def save_data(data):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except OSError as e:
        app.logger.error(f"Failed to save data: {e}")


def build_response(data):
    latest = data.get("latest")
    if not latest:
        return {
            "success": True,
            "kpis": {
                "total_scans": data.get("history_count", 0),
                "pass_rate": 0,
                "avg_dev": 0.000,
                "last_status": "READY"
            },
            "results": []
        }
    return {
        "success": True,
        "kpis": latest["kpis"],
        "results": latest["results"],
        "part_name": latest.get("part_name", ""),
        "timestamp": latest.get("timestamp", "")
    }


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/latest-result', methods=['GET'])
def latest_result():
    data = load_data()
    return jsonify(build_response(data))


@app.route('/api/submit-result', methods=['POST'])
def submit_result():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"success": False, "error": "Invalid or missing JSON payload."}), 400

    part_name = (payload.get('part_name') or 'Unnamed Part').strip()
    
    try:
        raw_tol = payload.get('tolerance')
        tolerance = abs(float(raw_tol)) if raw_tol not in (None, '') else DEFAULT_TOLERANCE
    except (TypeError, ValueError):
        tolerance = DEFAULT_TOLERANCE

    points = payload.get('points', [])
    if not isinstance(points, list) or not points:
        return jsonify({"success": False, "error": "No measurement points provided."}), 400

    results = []
    deviations = []
    for i, p in enumerate(points):
        if not isinstance(p, dict):
            continue
        try:
            dev = float(p.get('deviation'))
        except (TypeError, ValueError):
            return jsonify({"success": False, "error": f"Point {i+1} has an invalid deviation value."}), 400

        label = (p.get('label') or f"Point {i+1}").strip()
        status = "PASS" if abs(dev) <= tolerance else "FAIL"
        deviations.append(dev)
        results.append({
            "parameter": label,
            "nominal": 0.000,
            "measured": round(dev, 3),
            "deviation": round(dev, 3),
            "status": status
        })

    if not results:
        return jsonify({"success": False, "error": "Valid measurement points are required."}), 400

    overall_status = "PASS" if all(r["status"] == "PASS" for r in results) else "FAIL"
    avg_dev = round(sum(abs(d) for d in deviations) / len(deviations), 3)

    data = load_data()
    data["history_count"] = data.get("history_count", 0) + 1
    data["history_pass"] = data.get("history_pass", 0) + (1 if overall_status == "PASS" else 0)
    
    pass_rate = round(100 * data["history_pass"] / data["history_count"], 1)

    data["latest"] = {
        "part_name": part_name,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "kpis": {
            "total_scans": data["history_count"],
            "pass_rate": pass_rate,
            "avg_dev": avg_dev,
            "last_status": overall_status
        },
        "results": results
    }
    save_data(data)

    return jsonify(build_response(data))


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1')
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
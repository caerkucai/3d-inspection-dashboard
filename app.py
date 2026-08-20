from flask import Flask, render_template, redirect, url_for
import database
import random
import os

app = Flask(__name__)

# Initialize database
database.init_db()

def generate_qc_features(status):
    feature_definitions = [
        {"name": "Hole Ø1", "nominal": 6.00, "tolerance": 0.10},
        {"name": "Hole Ø2", "nominal": 6.00, "tolerance": 0.10},
        {"name": "Length A", "nominal": 120.00, "tolerance": 0.10},
        {"name": "Width B", "nominal": 50.00, "tolerance": 0.10},
        {"name": "Flatness", "nominal": 0.00, "tolerance": 0.10}
    ]

    features = []
    for feature in feature_definitions:
        dev = round(random.uniform(-0.05, 0.05), 2)
        features.append({
            "name": feature["name"],
            "nominal": feature["nominal"],
            "actual": round(feature["nominal"] + dev, 2),
            "deviation": dev,
            "tolerance": feature["tolerance"],
            "status": "PASS"
        })

    if status == "FAIL":
        fail_idx = random.randint(0, len(features) - 1)
        fail_dev = round(random.choice([random.uniform(0.12, 0.25), random.uniform(-0.25, -0.12)]), 2)
        features[fail_idx]["deviation"] = fail_dev
        features[fail_idx]["actual"] = round(features[fail_idx]["nominal"] + fail_dev, 2)
        features[fail_idx]["status"] = "FAIL"

    return features

def format_dev(val):
    return f"+{val:.2f} mm" if val > 0 else f"{val:.2f} mm"

@app.route("/")
def home():
    history = database.get_all_inspections()
    latest = database.get_latest()

    if latest is None:
        return "No inspection data available."

    features = database.get_measurements(latest["scan_id"])

    qc_data = {
        "part_id": latest["part_id"],
        "scan_id": latest["scan_id"],
        "inspection_date": latest["timestamp"],
        "status": latest["status"],
        "total_checked": len(history),
        "passed_count": sum(1 for i in history if i["status"] == "PASS"),
        "failed_count": sum(1 for i in history if i["status"] == "FAIL"),
        "max_deviation": latest["max_dev"],
        "min_deviation": latest["min_dev"],
        "features": features,
        "history": history
    }

    return render_template("index.html", qc=qc_data)

@app.route("/trigger_scan")
def trigger_scan():
    overall_status = random.choice(["PASS", "PASS", "PASS", "FAIL"])
    features = generate_qc_features(overall_status)

    devs = [f["deviation"] for f in features]
    part_id = f"PART-2026-X{random.randint(1, 5)}"

    database.add_new_scan(
        part_id=part_id,
        status=overall_status,
        max_dev=format_dev(max(devs)),
        min_dev=format_dev(min(devs)),
        features=features
    )

    return redirect(url_for("home"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
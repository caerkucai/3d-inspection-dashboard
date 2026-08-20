import os
import random
from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scan', methods=['POST'])
def trigger_scan():
    # Generate realistic 3D measurement deviations (in mm)
    dev_x = round(random.uniform(-0.04, 0.04), 3)
    dev_y = round(random.uniform(-0.05, 0.05), 3)
    dev_z = round(random.uniform(-0.03, 0.03), 3)
    
    status_x = "PASS" if abs(dev_x) <= 0.035 else "FAIL"
    status_y = "PASS" if abs(dev_y) <= 0.035 else "FAIL"
    status_z = "PASS" if abs(dev_z) <= 0.035 else "FAIL"
    
    overall_status = "PASS" if (status_x == "PASS" and status_y == "PASS" and status_z == "PASS") else "FAIL"

    return jsonify({
        "success": True,
        "kpis": {
            "total_scans": random.randint(18, 60),
            "pass_rate": round(random.uniform(93.0, 98.5), 1),
            "avg_dev": round((abs(dev_x) + abs(dev_y) + abs(dev_z)) / 3, 3),
            "last_status": overall_status
        },
        "results": [
            {"parameter": "Length X", "nominal": 120.000, "measured": round(120.000 + dev_x, 3), "deviation": dev_x, "status": status_x},
            {"parameter": "Width Y",  "nominal": 60.000,  "measured": round(60.000 + dev_y, 3),  "deviation": dev_y, "status": status_y},
            {"parameter": "Height Z", "nominal": 30.000,  "measured": round(30.000 + dev_z, 3),  "deviation": dev_z, "status": status_z}
        ]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
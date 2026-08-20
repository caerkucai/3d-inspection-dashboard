import sqlite3
import datetime

DB_NAME = "qc_database.db"

# ============================================================
# DATABASE CONNECTION
# ============================================================
def get_connection():
    """Create a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# ============================================================
# DATABASE INITIALIZATION
# ============================================================
def init_db():
    """Create the required database tables and seed initial data."""
    conn = get_connection()
    cursor = conn.cursor()

    # Inspection summary table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inspections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id TEXT NOT NULL,
            part_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            status TEXT NOT NULL,
            max_dev TEXT NOT NULL,
            min_dev TEXT NOT NULL
        )
    """)

    # Detailed measurement table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id TEXT NOT NULL,
            feature_name TEXT NOT NULL,
            nominal REAL NOT NULL,
            actual REAL NOT NULL,
            deviation REAL NOT NULL,
            tolerance REAL NOT NULL,
            status TEXT NOT NULL
        )
    """)
    conn.commit()

    # Seed inspections if empty
    cursor.execute("SELECT COUNT(*) FROM inspections")
    if cursor.fetchone()[0] == 0:
        seed_data = [
            ("SCAN-0819", "PART-2026-X1", "2026-08-19 15:20:00", "PASS", "+0.04 mm", "-0.02 mm"),
            ("SCAN-0818", "PART-2026-X1", "2026-08-19 15:12:00", "PASS", "+0.03 mm", "-0.01 mm"),
            ("SCAN-0817", "PART-2026-X0", "2026-08-19 14:45:00", "FAIL", "+0.15 mm", "-0.08 mm"),
            ("SCAN-0816", "PART-2026-X0", "2026-08-19 14:30:00", "PASS", "+0.02 mm", "-0.02 mm")
        ]
        cursor.executemany("""
            INSERT INTO inspections (scan_id, part_id, timestamp, status, max_dev, min_dev)
            VALUES (?, ?, ?, ?, ?, ?)
        """, seed_data)
        conn.commit()

    # Seed measurements if empty
    cursor.execute("SELECT COUNT(*) FROM measurements")
    if cursor.fetchone()[0] == 0:
        seed_measurements = [
            ("SCAN-0819", "Hole Ø1", 6.00, 6.02, 0.02, 0.10, "PASS"),
            ("SCAN-0819", "Hole Ø2", 6.00, 5.99, -0.01, 0.10, "PASS"),
            ("SCAN-0819", "Length A", 120.00, 120.04, 0.04, 0.10, "PASS"),
            ("SCAN-0819", "Width B", 50.00, 49.98, -0.02, 0.10, "PASS"),
            ("SCAN-0819", "Flatness", 0.00, 0.01, 0.01, 0.10, "PASS")
        ]
        cursor.executemany("""
            INSERT INTO measurements (scan_id, feature_name, nominal, actual, deviation, tolerance, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, seed_measurements)
        conn.commit()

    # FIXED: Always close the connection
    conn.close()

# ============================================================
# GET ALL INSPECTIONS
# ============================================================
def get_all_inspections():
    """Return all inspection records, newest first."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT scan_id, part_id, timestamp, status, max_dev, min_dev 
        FROM inspections ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    
    return [{
        "id": row["scan_id"],
        "part": row["part_id"],
        "time": row["timestamp"],
        "status": row["status"],
        "max_dev": row["max_dev"],
        "min_dev": row["min_dev"]
    } for row in rows]

# ============================================================
# GET LATEST INSPECTION
# ============================================================
def get_latest():
    """Return the newest inspection record."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT scan_id, part_id, timestamp, status, max_dev, min_dev 
        FROM inspections ORDER BY id DESC LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return {
        "scan_id": row["scan_id"],
        "part_id": row["part_id"],
        "timestamp": row["timestamp"],
        "status": row["status"],
        "max_dev": row["max_dev"],
        "min_dev": row["min_dev"]
    }

# ============================================================
# GET MEASUREMENTS FOR A SCAN
# ============================================================
def get_measurements(scan_id):
    """Return all dimensional measurements for a specific scan."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT feature_name, nominal, actual, deviation, tolerance, status
        FROM measurements WHERE scan_id = ? ORDER BY id ASC
    """, (scan_id,))
    rows = cursor.fetchall()
    conn.close()

    features = []
    for row in rows:
        dev_val = float(row["deviation"])
        dev_str = f"+{dev_val:.2f} mm" if dev_val > 0 else f"{dev_val:.2f} mm"
        features.append({
            "name": row["feature_name"],
            "nominal": f"{row['nominal']:.2f} mm",
            "actual": f"{row['actual']:.2f} mm",
            "dev": dev_str,
            "dev_raw": dev_val,
            "tolerance": row["tolerance"],
            "status": row["status"]
        })
    return features

# ============================================================
# ADD NEW INSPECTION
# ============================================================
def add_new_scan(part_id, status, max_dev, min_dev, features):
    """Insert a new inspection and its individual measurements."""
    conn = get_connection()
    cursor = conn.cursor()

    # FIXED: Adjusted offset formula to prevent gap after SCAN-0819
    cursor.execute("SELECT COUNT(*) FROM inspections")
    count = cursor.fetchone()[0]
    next_number = 816 + count
    scan_id = f"SCAN-0{next_number}" if next_number < 1000 else f"SCAN-{next_number}"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO inspections (scan_id, part_id, timestamp, status, max_dev, min_dev)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (scan_id, part_id, timestamp, status, max_dev, min_dev))

    for feature in features:
        cursor.execute("""
            INSERT INTO measurements (scan_id, feature_name, nominal, actual, deviation, tolerance, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            scan_id,
            feature["name"],
            feature["nominal"],
            feature["actual"],
            feature["deviation"],
            feature["tolerance"],
            feature["status"]
        ))

    conn.commit()
    conn.close()
    return scan_id
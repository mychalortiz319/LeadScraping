from flask import Flask, request, jsonify
import sqlite3
import os
import re

app = Flask(__name__)

# ✅ Ensure the database and table exist
def initialize_db():
    """Creates the cik_mapping.db database and ensures cik_lookup table exists."""
    DB_PATH = os.path.join(os.getcwd(), "cik_mapping.db")  # Ensure correct path
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create cik_lookup table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cik_lookup (
            company_name TEXT PRIMARY KEY,
            cik TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database before starting the app
initialize_db()

# ✅ Normalize function
def normalize_company_name(name):
    """Normalize company names by removing common suffixes and punctuation."""
    if not isinstance(name, str):  # Ensure input is a string
        return None

    name = name.upper().strip()
    suffixes = [" INC", " LLC", " CORP", " CORPORATION", " LTD", " LIMITED", " LP", " L.P."]

    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    
    # Remove punctuation
    name = re.sub(r'[^A-Z0-9 ]', '', name)

    return name

# ✅ SQLite connection
def get_cik(company_name):
    """Fetch CIK from SQLite database."""
    DB_PATH = os.path.join(os.getcwd(), "cik_mapping.db")  # Ensure correct path
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    normalized_name = normalize_company_name(company_name)
    if not normalized_name:
        return None

    cursor.execute("SELECT cik FROM cik_lookup WHERE company_name = ?", (normalized_name,))
    result = cursor.fetchone()

    conn.close()
    
    return result[0] if result else None

# ✅ Flask API endpoint
@app.route("/get_cik", methods=["GET"])
def fetch_cik():
    try:
        company_name = request.args.get("company")
        
        if not company_name:
            return jsonify({"error": "Company name required"}), 400

        cik = get_cik(company_name)
        
        return jsonify({"cik": cik}) if cik else jsonify({"error": "CIK not found"}), 404
    except Exception as e:
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)  # Render prefers port 10000 or 8080

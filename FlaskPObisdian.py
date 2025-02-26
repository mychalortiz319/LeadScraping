from flask import Flask, request, jsonify
import sqlite3
import re

app = Flask(__name__)

# Normalize function
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

# SQLite connection
def get_cik(company_name):
    """Fetch CIK from SQLite."""
    conn = sqlite3.connect("cik_mapping.db")
    cursor = conn.cursor()
    
    normalized_name = normalize_company_name(company_name)
    if not normalized_name:
        return None

    cursor.execute("SELECT cik FROM cik_lookup WHERE company_name = ?", (normalized_name,))
    result = cursor.fetchone()

    conn.close()
    
    return result[0] if result else None

# Flask API endpoint
@app.route("/get_cik", methods=["GET"])
def fetch_cik():
    company_name = request.args.get("company")
    
    if not company_name:
        return jsonify({"error": "Company name required"}), 400

    cik = get_cik(company_name)
    
    return jsonify({"cik": cik}) if cik else jsonify({"error": "CIK not found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
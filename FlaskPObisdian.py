from flask import Flask, request, jsonify
import sqlite3
import os
import re
from fuzzywuzzy import process

app = Flask(__name__)

# ✅ Ensure database and table exist
def initialize_db():
    DB_PATH = os.path.join(os.getcwd(), "cik_mapping.db")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cik_lookup (
            company_name TEXT PRIMARY KEY,
            cik TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

initialize_db()

# ✅ Normalize function
def normalize_company_name(name):
    """Normalize company names by removing common suffixes and punctuation."""
    if not isinstance(name, str):
        return None

    name = name.upper().strip()
    suffixes = [" INC", " LLC", " CORP", " CORPORATION", " LTD", " LIMITED", " LP", " L.P."]

    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    
    name = re.sub(r'[^A-Z0-9 ]', '', name)

    return name

# ✅ Fetch all SEC names and their CIKs from the database
def get_sec_data():
    DB_PATH = os.path.join(os.getcwd(), "cik_mapping.db")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT company_name, cik FROM cik_lookup")
    sec_data = {row[0]: row[1] for row in cursor.fetchall()}  # Dictionary: {Company Name: CIK}
    
    conn.close()
    
    return sec_data

# ✅ Fuzzy matching function with CIK retrieval
def find_best_match_and_cik(company_name, sec_data):
    """Find the best fuzzy match and return its CIK if confidence is high."""
    normalized_name = normalize_company_name(company_name)
    
    if not normalized_name:
        return None, None

    sec_names = list(sec_data.keys())
    best_match, score = process.extractOne(normalized_name, sec_names)

    if score >= 85:  # Adjust threshold as needed
        return best_match, sec_data[best_match]
    
    return None, None

# ✅ New endpoint to find the best fuzzy match and return its CIK
@app.route("/get_cik", methods=["GET"])
def fetch_cik():
    try:
        company_name = request.args.get("company")

        if not company_name:
            return jsonify({"error": "Company name required"}), 400

        sec_data = get_sec_data()  # Fetch SEC company names and CIKs
        best_match, cik = find_best_match_and_cik(company_name, sec_data)

        if cik:
            return jsonify({"cik": cik, "matched_company": best_match})
        else:
            return jsonify({"error": "No good match found"}), 404

    except Exception as e:
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)  # Render prefers port 10000 or 8080

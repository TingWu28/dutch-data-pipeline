import requests
import csv
import os
from datetime import datetime

# API configuration
STATION_ID = "260"
START_DATE = "20240101"
END_DATE = "20241231"
OUTPUT_DIR = "data"

def fetch_knmi_data(station_id, start_date, end_date):
    url = "https://www.daggegevens.knmi.nl/klimatologie/daggegevens"
    params = {
        "stns": station_id,
        "start": start_date,
        "end": end_date,
        "vars": "TG:RH:FG"
    }
    response = requests.get(url, params = params)
    response.raise_for_status()
    return response.text

def save_to_csv(raw_text, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    filename = f"knmi_260_{datetime.now().strftime('%Y%m%d')}.csv"
    filepath = os.path.join(output_dir, filename) # never hardcode / or \

    lines = [l for l in raw_text.splitlines() if not l.startswith("#") and l.strip()] # if not xx and yy is interpreted as (not xx) and (yy), l.strip(): is the line non-empty

    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        for line in lines:
            writer.writerow([col.strip() for col in line.split(",")])

    print(f"Saved {len(lines)} rows to {filepath}")
    return filepath

def main():
    '''ties the two functions together. 
    Clean separation: one function fetches, one saves, main orchestrates. 
    Thisis how engineers structure scripts.'''
    raw = fetch_knmi_data(STATION_ID, START_DATE, END_DATE)
    save_to_csv(raw, OUTPUT_DIR)

if __name__ == "__main__":
    '''this block only runs when you execute the file directly (python knmi_ingest.py). 
    If another script imports this file later, it won't auto-execute. 
    Always use this pattern for scripts'''
    main()
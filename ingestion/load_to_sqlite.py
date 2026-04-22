import sqlite3
import csv
import os
import glob

output_dir = "data"
files = glob.glob("data/knmi_*.csv")
filepath = files[0]

with open(filepath, "r") as f:
    reader = csv.reader(f)
    rows = [(int(row[0]), row[1], int(row[2]), int(row[3]), int(row[4])) for row in reader]



con = sqlite3.connect("data/knmi.db")
cur = con.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS daily_weather
            (
            station_id INTEGER,
            date TEXT,
            TG INTEGER,
            RH INTEGER,
            FG INTEGER)
""")

cur.executemany("INSERT INTO daily_weather VALUES (?,?,?,?,?)", rows)
con.commit()
con.close()

print(f"Loaded {len(rows)} rows into daily_weather")


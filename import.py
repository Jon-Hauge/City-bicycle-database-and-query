# Used to import data from bysykkel.csv into the bysykkel.db
# Does not need to be run unless database somehow errors, in which case
# delete the database file from your directory, run table_creation.py
# and then run this file. 

import sqlite3
import csv

con = sqlite3.connect("bysykkel.db")
cur = con.cursor()

cur.execute("PRAGMA foreign_keys = ON;")
cur.execute("PRAGMA journal_mode = WAL;")
cur.execute("PRAGMA synchronous = OFF;")

# Importing bysykkel.csv

# Parts of the following code was formulated / helped by OpenAI's ChatGPT
# This includes the idea of using dicts/sets to import data and the
# code for the status-map / new_bikes.
# All code helped by AI is understood in and of itself and in relation to the rest of the program
# OpenAI - https://chatgpt.com - retrieved 01.03.2026

stations = {}
users = {}
bikes = {}
subscriptions = {}
trips = {}
statuses = set()

with open("bysykkel.csv", newline='', encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)

    for row in reader:
        
        if row["start_station_id"]:
            sid = int(row["start_station_id"])
            stations[sid] = (sid,
                             row["start_station_name"],
                             float(row["start_station_latitude"]) if row["start_station_latitude"] else None,
                             float(row["start_station_longitude"]) if row["start_station_longitude"] else None,
                             int(row["start_station_max_spots"]) if row["start_station_max_spots"] else None)
        
        if row["end_station_id"]:
            sid = int(row["end_station_id"])
            stations[sid] = (sid,
                             row["end_station_name"],
                             float(row["end_station_latitude"]) if row["end_station_latitude"] else None,
                             float(row["end_station_longitude"]) if row["end_station_longitude"] else None,
                             int(row["end_station_max_spots"]) if row["end_station_max_spots"] else None)

        if row["user_id"]:
            uid = int(row["user_id"])
            users[uid] = (uid, 
                        row["user_name"],
                        row["user_phone_number"],
                        None, None)
        
        valid_statuses = {'Active', 'Parked', 'Missing', 'Service'}
        status = row["bike_status"]

        if status:
            if status in valid_statuses:
                statuses.add(row["bike_status"])

        if row["bike_id"]:
            bid = int(row["bike_id"])
            bikes[bid] = (bid,
                        row["bike_name"],
                        int(row["bike_station_id"]) if row["bike_station_id"] else None,
                        status if status in valid_statuses else None)
        
        if row["subscription_id"]:
            sid = int(row["subscription_id"])
            subscriptions[sid] = (sid,
                                int(row["user_id"]) if row["user_id"] else None,
                                "Active",
                                row["subscription_start_time"],
                                None,
                                row["subscription_type"])
        
        if row["trip_id"]:
            tid = int(row["trip_id"])
            trips[tid] = (tid,
                        int(row["user_id"]) if row["user_id"] else None,
                        int(row["bike_id"]) if row["bike_id"] else None,
                        row["trip_start_time"],
                        row["trip_end_time"] or None,
                        int(row["start_station_id"]) if row["start_station_id"] else None,
                        int(row["end_station_id"]) if row["end_station_id"] else None)
        
with con:

    cur.executemany("INSERT INTO Station(" \
                    "StationID, Name, Latitude, Longitude, MaxParking) " \
                    "VALUES (?, ?, ?, ?, ?)", stations.values())
    
    cur.executemany("INSERT INTO User(" \
                    "UserID, Name, PhoneNr, Latitude, Longitude) " \
                    "VALUES (?, ?, ?, ?, ?)", users.values())
    
    cur.executemany("INSERT INTO BikeStatus (StatusName) "
                    "VALUES (?)", [(status,) for status in statuses])
    
    cur.execute("SELECT StatusID, StatusName FROM BikeStatus")
    status_map = {name : sid for sid, name in cur.fetchall()}

    new_bikes = [(b[0], b[1], b[2], status_map[b[3]] if b[3] in status_map else None) for b in bikes.values()]

    cur.executemany("INSERT INTO Bike(" \
                    "BikeID, Name, LastStationID, StatusID) " \
                    "VALUES (?, ?, ?, ?)", new_bikes)
    
    cur.executemany("INSERT INTO Subscriptions (" \
                    "SubscriptionID, UserID, Status, StartDate, EndDate, Type) " \
                    "VALUES (?, ?, ?, ?, ?, ?)", subscriptions.values())
    
    cur.executemany("INSERT INTO Trips(" \
                    "TripID, UserID, BikeID, StartTime, EndTime, StartStationID, EndStationID) " \
                    "VALUES (?, ?, ?, ?, ?, ?, ?)", trips.values())
    
con.close()
print("Imported data successfully")
# Used to create the bysykkel.db database file.
# Does not need to be run unless database somehow errors, 
# in which case, delete the old bysykkel.db, run this first, then import.py.

import sqlite3

con = sqlite3.connect("bysykkel.db")
cur = con.cursor()
cur.execute("PRAGMA foreign_keys = ON;")

# Creating tables

# Bike
bike_query = "CREATE TABLE IF NOT EXISTS Bike(" \
                "BikeID INTEGER PRIMARY KEY AUTOINCREMENT, " \
                "Name VARCHAR NOT NULL, " \
                "LastStationID INTEGER, " \
                "StatusID INTEGER, " \
                "FOREIGN KEY (LastStationID) REFERENCES Station (StationID), " \
                "FOREIGN KEY (StatusID) REFERENCES BikeStatus (StatusID));"

# User
user_query = "CREATE TABLE IF NOT EXISTS User(" \
                "UserID INTEGER, " \
                "Name VARCHAR NOT NULL, " \
                "PhoneNr VARCHAR, " \
                "Latitude FLOAT(10,6), " \
                "Longitude FLOAT(10,6), " \
                "PRIMARY KEY (UserID));"

# Station
station_query = "CREATE TABLE IF NOT EXISTS Station(" \
                "StationID INTEGER UNIQUE NOT NULL, " \
                "Name VARCHAR NOT NULL, " \
                "Latitude FLOAT(10,6), " \
                "Longitude FLOAT(10,6), " \
                "MaxParking SMALLINT NOT NULL, " \
                "PRIMARY KEY (StationID));"

# Subscriptions 
subscriptions_query = "CREATE TABLE IF NOT EXISTS Subscriptions(" \
                "SubscriptionID INTEGER, " \
                "UserID INTEGER NOT NULL, " \
                "Status VARCHAR NOT NULL, " \
                "StartDate VARCHAR NOT NULL, " \
                "EndDate VARCHAR, " \
                "Type VARCHAR NOT NULL, " \
                "PRIMARY KEY (SubscriptionID), " \
                "FOREIGN KEY (UserID) REFERENCES User (UserID));"

# Trips
trips_query = "CREATE TABLE IF NOT EXISTS Trips(" \
                "TripID INTEGER, " \
                "UserID INTEGER NOT NULL, " \
                "BikeID INTEGER NOT NULL, " \
                "StartTime VARCHAR NOT NULL, " \
                "EndTime VARCHAR, " \
                "StartStationID INTEGER NOT NULL, " \
                "EndStationID INTEGER, " \
                "PRIMARY KEY (TripID), " \
                "FOREIGN KEY (UserID) REFERENCES User (UserID), " \
                "FOREIGN KEY (BikeID) REFERENCES Bike (BikeID), " \
                "FOREIGN KEY (StartStationID) REFERENCES Station (StationID), " \
                "FOREIGN KEY (EndStationID) REFERENCES Station (StationID));"

# Complaint
complaint_query = "CREATE TABLE IF NOT EXISTS Complaint(" \
                "ComplaintID INTEGER, " \
                "BikeID INTEGER NOT NULL, " \
                "UserID INTEGER NOT NULL, " \
                "ComplaintTypeID INTEGER NOT NULL, " \
                "DateReported VARCHAR NOT NULL, " \
                "PRIMARY KEY (ComplaintID), " \
                "FOREIGN KEY (BikeID) REFERENCES Bike (BikeID), " \
                "FOREIGN KEY (UserID) REFERENCES User (UserID), " \
                "FOREIGN KEY (ComplaintTypeID) REFERENCES ComplaintType (ComplaintTypeID));"

# Parts of the following code was formulated / helped by OpenAI's ChatGPT
# This includes the use of autoincrementing for the complaint_type and bike_status
# All code helped by AI is understood in and of itself and in relation to the rest of the program
# OpenAI - https://chatgpt.com - retrieved 01.03.2026

# ComplaintType
complaint_type_query = "CREATE TABLE IF NOT EXISTS ComplaintType(" \
                "ComplaintTypeID INTEGER PRIMARY KEY AUTOINCREMENT , " \
                "Name VARCHAR UNIQUE NOT NULL);"

# BikeStatus
bike_status_query = "CREATE TABLE IF NOT EXISTS BikeStatus(" \
                "StatusID INTEGER PRIMARY KEY AUTOINCREMENT , " \
                "StatusName VARCHAR UNIQUE NOT NULL " \
                "CHECK (StatusName IN ('Active', 'Parked', 'Missing', 'Service')));"


# Executing queries
cur.execute(station_query)
cur.execute(bike_status_query)
cur.execute(user_query)
cur.execute(bike_query)
cur.execute(subscriptions_query)
cur.execute(trips_query)
cur.execute(complaint_type_query)
cur.execute(complaint_query)

# Committing changes
con.commit()
con.close()

print("Database changes were successfull!")
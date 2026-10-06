# Use the following line in a terminal to run the application:
# shiny run --reload --launch-browser app.py

from shiny.express import ui, render, input
from shiny import reactive, render
import sqlite3
import pandas as pd

con = sqlite3.connect("bysykkel.db")
cur = con.cursor()

# Parts of the following code was formulated / helped by OpenAI's ChatGPT
# This includes use of reactive.Value to refresh tables, the COALESCE-function in
# StationView, displaying all values of filterable tables before filter button is pressed,
# updating lists of choosable elements in real time via @render.ui, using the RANDOM() and
# WHERE NOT EXISTS (SELECT 1 FROM Complaint)-functions for adding complaints into the database,
# and appending strings into queries to display position.
# All code helped by AI is understood in and of itself and in relation to the rest of the program
# OpenAI - https://chatgpt.com - retrieved 14.04.2026

# Other code was helped by previous tasks and documentation on shiny.
# Posit - https://shiny.posit.co/py/api/express/ - retrieved 14.04.2026

# Add refresh value to update tables in real-time
refresh = reactive.Value(0)

with ui.navset_tab():
    with ui.nav_panel("Viewing tables"):
        # 1
        # a) + 3a) + 3b)

        statuses = ['Active', 'Parked', 'Missing', 'Service']
        ui.input_select("status", "Choose status", statuses)
        ui.input_action_button("filter_status", "Filter", class_="btn-success")

        @render.table
        @reactive.event(input.filter_status, ignore_none=False)
        def result_1a():
            refresh.get()

            # Show all bikes initally
            if input.filter_status() == 0:
                return pd.read_sql_query("""
                        SELECT B.Name AS BikeName, B.BikeID, BS.StatusName AS BikeStatus
                         FROM Bike B LEFT JOIN BikeStatus BS ON B.StatusID = BS.StatusID
                         ORDER BY B.Name ASC;
                        """, con)
            
            return pd.read_sql_query("""
                    SELECT B.Name AS BikeName, B.BikeID, BS.StatusName AS BikeStatus
                     FROM Bike B LEFT JOIN BikeStatus BS ON B.StatusID = BS.StatusID
                     WHERE BS.StatusName = ?
                     ORDER BY B.Name ASC;
                    """, con, params=(input.status(),))


        # b)

        # We first create a view of the stations with available parking as
        # an added attribute derived from max parking and parked bikes.
        # Dropping it if it exists makes sure NaN-values are avoided.

        _ = cur.execute("""
                        DROP VIEW IF EXISTS StationView;
                        """)

        # Using COALESCE avoids available parking being null
        _ = cur.execute("""
                        CREATE VIEW IF NOT EXISTS StationView AS
                         SELECT S.StationID, S.Name, S.MaxParking, 
                         (S.MaxParking - COALESCE(CNT.OccupiedSpots, 0)) AS AvailableParking
                         FROM Station S LEFT JOIN (
                        SELECT B.LastStationID, COUNT(*) AS OccupiedSpots
                         FROM Bike B JOIN BikeStatus BS ON B.StatusID = BS.StatusID
                         WHERE BS.StatusName = 'Parked' AND B.LastStationID IS NOT NULL
                         GROUP BY B.LastStationID) CNT ON S.StationID = CNT.LastStationID;
                        """)

        @render.table
        def result_1b():
            refresh.get()

            return pd.read_sql_query("""
                    SELECT S.Name AS StationName, S.StationID, S.MaxParking, S.AvailableParking,
                    ROUND((S.AvailableParking * 100 / S.MaxParking), 3) || '%'
                     AS AvailableParkingPercentage
                     FROM StationView S
                     GROUP BY S.Name, S.StationID, S.MaxParking;
                    """, con)


        # c)

        @render.table
        def result_1c():
            refresh.get()

            return pd.read_sql_query("""
                    SELECT Type AS SubscriptionType, Count(*) as PurchasedSubs
                     FROM Subscriptions
                     WHERE Type IN ('Year', 'Month', 'Week', 'Day')
                     GROUP BY Type
                     ORDER BY PurchasedSubs DESC;
                    """, con)


# 2

# a)
# When creating the database initally, I made a separate table for the bike's status,
# named BikeStatus. The query for creating this table was:

# bike_status_query = """
#                   CREATE TABLE IF NOT EXISTS BikeStatus(
#                   StatusID INTEGER PRIMARY KEY AUTOINCREMENT,
#                   StatusName VARCHAR UNIQUE NOT NULL);
#                   """

# To enforce that the bikes can only have one of the four provided values, Active
# Parked, Missing or Service, we change the query slightly to fit this new constraint. 

# bike_status_query = """
#                   CREATE TABLE IF NOT EXISTS BikeStatus(
#                   StatusID INTEGER PRIMARY KEY AUTOINCREMENT,
#                   StatusName VARCHAR UNIQUE NOT NULL
#                    CHECK (StatusName IN ('Active', 'Parked', 'Missing', 'Service')));
#                   """

# With this, we successfully alter the database to enforce bikes needing to have one of the four 
# bike statuses. However, this change also required some changes to the data-filtering process
# done before importing the values from bysykkel.csv. Previously, this was the line used
# to add the values from the csv to a premade dictionary:
 
# statuses.add(row["bike_status"])

# Before inserting it into BikeStatus via this query:

# with con:
#   ...
#   cur.executemany("""INSERT INTO BikeStatus (StatusName)
#                    VALUES (?)""", [(status,) for status in statuses])


# To ensure we get no errors with the new table, we must change it
# to filter out null/NaN values:

# valid_statuses = {'Active', 'Parked', 'Missing', 'Service'}
# status = row["bike_status"]

# if status:
#    if status in valid_statuses:
#       statuses.add(row["bike_status"])

# Inserting uses the same code as before.
# The database used in this mandatory uses the same .py-files
# and csv from the previous mandatory + these new changes.


    # b) + c)

    # Initiates an ID for the Service status via the autoincrementing primary key
    # since it does not already exist in bysykkel.csv
    _ = cur.execute("""
                    INSERT OR IGNORE INTO BikeStatus (StatusName) VALUES (?);
                    """, ('Service',))

    con.commit()

    with ui.nav_panel("Add a Bike"):
        ui.input_text("name", "Name:", "")
        ui.input_action_button("submit", "Submit", width='150px', class_="btn-success")
            
        @reactive.effect
        @reactive.event(input.submit, ignore_none=True)
        def btn_add_bike():
            try:
                # Only add name if it consists of letters.
                # Double names are allowed, hence the spacebar is included.
                can_be_added = True

                if len(input.name()) == 0:
                        can_be_added = False

                for i in range(len(input.name())):
                    if input.name()[i].lower() in 'abcdefghijklmnopqrstuvwxyzæøå ':
                        continue
                    else: can_be_added = False
                            
                if can_be_added:
                        cur.execute("""
                                    SELECT StatusID From BikeStatus WHERE StatusName = 'Service';
                                    """)
                        status_id = cur.fetchone()[0]

                        cur.execute("""
                                    INSERT INTO Bike (Name, LastStationID, StatusID)
                                     VALUES (?, NULL, ?);
                                    """, (input.name(), status_id))
                        
                        con.commit()
                        refresh.set(refresh.get() + 1)
                        ui.notification_show("Bike was added!")
                else: 
                    ui.notification_show("Name cannot include other characters than letters")

            except sqlite3.Error as err:
                con.rollback()
                ui.notification_show(f"SQLite Error: {err}", duration=None)


    # 3

    # a) - Changes are done within the scope of 1a)
    # b) - Changes are done within the scope of 1a)

    # c)
    with ui.nav_panel("Stations"):
        
        @render.ui
        def get_station_names():
            refresh.get()

            df = pd.read_sql_query("""
                    SELECT Name AS StationName FROM Station;
                    """, con)
            stationNames = df["StationName"].tolist()

            return ui.input_select("station", "Choose station", stationNames)

        ui.input_action_button("filter_stations", "Filter", class_="btn-success")

        @render.table
        @reactive.event(input.filter_stations, ignore_none=False)
        def result_3c():
            refresh.get()

            if input.filter_stations() == 0:
                return pd.read_sql_query("""
                        SELECT S.Name AS StationName, B.Name AS AvailableBikes
                         FROM Station S LEFT JOIN Bike B ON S.StationID = B.LastStationID
                         LEFT JOIN BikeStatus BS ON B.StatusID = BS.StatusID 
                         WHERE BS.StatusName = 'Parked';
                        """, con)

            return pd.read_sql_query("""
                    SELECT S.Name AS StationName, B.Name AS AvailableBikes
                     FROM Station S LEFT JOIN Bike B ON S.StationID = B.LastStationID
                     LEFT JOIN BikeStatus BS ON B.StatusID = BS.StatusID 
                     WHERE S.Name = ? AND BS.StatusName = 'Parked';
                    """, con, params=(input.station(),))


    # 4

    # a)
    with ui.nav_panel("Pick Up"):

        @render.ui
        def get_parked_bikes():
            refresh.get()
                    
            df = pd.read_sql_query("""
                    SELECT B.Name AS BikeName, B.BikeID, S.Name AS StationName
                     FROM Bike B LEFT JOIN BikeStatus BS ON B.StatusID = BS.StatusID
                     LEFT JOIN Station S ON B.LastStationID = S.StationID
                     WHERE BS.StatusName = 'Parked';
                    """, con)
            
            parked_bikes = {
                row['BikeID']: f"{row['BikeName']} ({row['BikeID']}, {row['StationName']})"
                for _, row in df.iterrows()
            }

            return ui.input_select("parked_bike", "Pick up bike", parked_bikes)
                
        ui.input_action_button("pick_up", "Pick up", width='150px', class_="btn-success")
                
        @reactive.effect
        @reactive.event(input.pick_up, ignore_none=True)
        def btn_pick_up():
            refresh.get()

            try:
                cur.execute("""
                            UPDATE Bike SET StatusID =
                             (SELECT StatusID FROM BikeStatus WHERE StatusName = 'Service')
                             WHERE BikeID = ?;
                            """, (input.parked_bike(),))
                        
                con.commit()
                refresh.set(refresh.get() + 1)
                ui.notification_show("Bike was picked up successfully!")

            except sqlite3.Error as err:
                con.rollback()
                ui.notification_show(f"SQLite Error: {err}", duration=None)


    # b)

    # Initates three different complaint-types via the autoincrementing primary key
    # since they do not already exist in bysykkel.csv.
    # Used the example complaint-types outlined in mandatory 1.
    _ = cur.execute("""
                    INSERT OR IGNORE INTO ComplaintType(Name) VALUES (?);
                    """, ('flat tire', ))
    _ = cur.execute("""
                    INSERT OR IGNORE INTO ComplaintType(Name) VALUES (?);
                    """, ('brakes not working', ))
    _ = cur.execute("""
                    INSERT OR IGNORE INTO ComplaintType(Name) VALUES (?);
                    """, ('gear not working', ))


    # Inserts the complaints into the Complaint table in the database.
    # We choose a random user to assert the complaint to.
    _ = cur.execute("""
                    INSERT INTO Complaint(BikeID, UserID, ComplaintTypeID, DateReported)
                     SELECT B.BikeID,
                     (SELECT UserID FROM User ORDER BY RANDOM() LIMIT 1),
                     CT.ComplaintTypeID,
                     datetime('now')
                     FROM (
                    SELECT BikeID FROM BIKE B JOIN BikeStatus BS ON B.StatusID = BS.StatusID
                     WHERE BS.StatusName = 'Parked'
                     ORDER BY RANDOM()
                     LIMIT 3) B
                     JOIN ComplaintType CT ON CT.Name IN (
                    'flat tire', 'brakes not working', 'gear not working')
                     WHERE NOT EXISTS (SELECT 1 FROM Complaint);
                    """)

    con.commit()


    # c)

    with ui.nav_panel("Service"):    
        
        @render.table
        def btn_show_complaints():
           refresh.get()

           if input.service_bike() is None:
                return pd.DataFrame()
           
           return pd.read_sql_query("""
                    SELECT C.ComplaintID, CT.Name AS ComplaintType, U.Name AS Username, C.DateReported
                     FROM Complaint C JOIN ComplaintType CT ON C.ComplaintTypeID = CT.ComplaintTypeID
                     JOIN USER U ON C.UserID = U.UserID
                     WHERE C.BikeID = ?; 
                    """, con, params=(input.service_bike(),))

        @render.ui
        def get_servicable_bikes():
            refresh.get()

            df = pd.read_sql_query("""
                    SELECT B.Name, B.BikeID
                     FROM Bike B LEFT JOIN BikeStatus BS ON B.StatusID = BS.StatusID
                     WHERE BS.StatusName = 'Service';
                    """, con)
            
            servicable_bikes = {
                row['BikeID']: f"{row['Name']} ({row['BikeID']})"
                for _, row in df.iterrows()
            }

            return ui.input_select("service_bike", "Select bike", servicable_bikes)
                
        @render.ui
        def get_available_stations():
            refresh.get()
            
            df = pd.read_sql_query("""
                    SELECT Name, StationID
                     FROM StationView
                     WHERE AvailableParking > 0;
                    """, con)
            
            available_stations = {
                row['StationID']: f"{row['Name']} ({row['StationID']})"
                for _, row in df.iterrows()
            }

            return ui.input_select("station_post_service", "Choose station", available_stations)
        
        ui.input_action_button("service_complaints", "Service complaints", width='150px', class_="btn-success")

        @render.table
        @reactive.event(input.service_complaints, ignore_none=True)
        def btn_service_complaints():
            refresh.get()

            try:
                if (input.service_bike() is not None):
                    cur.execute("""
                                DELETE FROM Complaint WHERE BikeID = ?;
                                """, (input.service_bike(), ))
                    cur.execute("""
                                UPDATE Bike SET LastStationID = ?
                                 WHERE BikeID = ?;
                                """, (input.station_post_service(), input.service_bike(), ))
                    cur.execute("""
                                UPDATE Bike SET StatusID = 
                                 (SELECT StatusID FROM BikeStatus WHERE StatusName = 'Parked')
                                 WHERE BikeID = ?;
                                """, (input.service_bike(), ))
                    
                    con.commit()
                    refresh.set(refresh.get() + 1)
                    ui.notification_show("Bike was serviced successfully!")
            
            except sqlite3.Error as err:
               con.rollback()
               ui.notification_show(f"SQLite Error: {err}", duration=None)              


    # 5

    with ui.nav_panel("Trips"):
            
        @render.table(render_links=True, escape=False)
        def trips():
            refresh.get()
            return pd.read_sql_query("""
                    SELECT S.Name, COUNT(DISTINCT T1.TripID) AS TripsStarted,
                     COUNT(DISTINCT T2.TripID) AS TripsEnded,
                     '<a href="https://www.openstreetmap.org/#map=17/' || S.LATITUDE || '/' || S.LONGITUDE ||'
                     "target = "_blank">Position</a>' AS Position
                     FROM Station S LEFT JOIN Trips T1 ON S.StationID = T1.StartStationID
                     LEFT JOIN Trips T2 ON S.StationID = T2.EndStationID
                     GROUP BY S.StationID, S.Name;
                    """, con)
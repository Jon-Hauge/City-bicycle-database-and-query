import sqlite3

con = sqlite3.connect("bysykkel.db")
cur = con.cursor()

sub_type_query = "SELECT Type, Count(*) as PurchasedSubs " \
                "FROM Subscriptions " \
                "WHERE Type IN ('Year', 'Month', 'Week', 'Day') " \
                "GROUP BY Type " \
                "ORDER BY PurchasedSubs DESC;"

cur.execute(sub_type_query)

results = cur.fetchall()

for sub_type, count in results:
    print(f"{sub_type} : {count}")
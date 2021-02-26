import sqlite3
import os
import csv

try:
    from settings import db_location
except:
    from pyzipcode.settings import db_location

conn = sqlite3.connect(db_location)
c = conn.cursor()

c.execute("DROP TABLE IF EXISTS FSACodes;")
c.execute(
    "CREATE TABLE FSACodes(fsa VARCHAR(3), city TEXT, province TEXT, longitude DOUBLE, latitude DOUBLE, accuracy INT);"
)
c.execute("CREATE INDEX fsa_index ON FSACodes(fsa);")
c.execute("CREATE INDEX city_index ON FSACodes(city);")
c.execute("CREATE INDEX province_index ON FSACodes(province);")


with open("CA.txt", newline="", encoding="utf-8") as f:
    reader = csv.reader(f, delimiter="\t")
    for row in reader:
        # country code      : iso country code, 2 characters
        # postal code       : varchar(20)
        # place name        : varchar(180)
        # admin name1       : 1. order subdivision (state) varchar(100)
        # admin code1       : 1. order subdivision (state) varchar(20)
        # admin name2       : 2. order subdivision (county/province) varchar(100)
        # admin code2       : 2. order subdivision (county/province) varchar(20)
        # admin name3       : 3. order subdivision (community) varchar(100)
        # admin code3       : 3. order subdivision (community) varchar(20)
        # latitude          : estimated latitude (wgs84)
        # longitude         : estimated longitude (wgs84)
        # accuracy          : accuracy of lat/lng from 1=estimated, 4=geonameid, 6=centroid of addresses or shape

        # TODO: use administrative subdivisions. The 3rd level is used in Quebec
        # For the other provinces, the second level usually holds the city/town
        # the "code" for those is some 7 digit number I've never seen before.
        _, fsa, city, province, province_code, _, _, _, _, lat, longt, accuracy = row

        c.execute(
            "INSERT INTO FSACodes values(?,?,?,?,?,?,?)",
            fsa, city, province, province_code, float(lat), float(longt), accuracy
        )

conn.commit()

# We can also close the cursor if we are done with it
c.close()

import sqlite3
import os
import csv
import sys

try:
    from settings import db_location
except:
    from postalcodes_ca.settings import db_location

conn = sqlite3.connect(db_location)
c = conn.cursor()

c.execute("DROP TABLE IF EXISTS FSACodes;")
c.execute("""\
CREATE TABLE FSACodes(
    fsa VARCHAR(3) NOT NULL,
    name VARCHAR(180) NOT NULL,
    province VARCHAR(100) NOT NULL,
    latitude DOUBLE NOT NULL,
    longitude DOUBLE NOT NULL,
    accuracy INT
);""")
c.execute("CREATE INDEX fsa_index ON FSACodes(fsa);")
c.execute("CREATE INDEX name_index ON FSACodes(name);")
c.execute("CREATE INDEX province_index ON FSACodes(province);")


with open("CA.tsv", newline="", encoding="utf-8") as f:
    reader = csv.reader(f, delimiter="\t")
    for idx, row in enumerate(reader, start=1):
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
        country_code, fsa, name, province, province_code, _, _, _, _, lat, longt, accuracy, = row

        if country_code != "CA":
            sys.exit(f"invalid country code {country_code!r} in row {idx}")

        for var, val in [("fsa", fsa), ("name", name), ("province", province), ("province_code", province_code), ("lat", lat), ("longt", longt)]:
            if val != val.strip():
                print(var, "contains whitespace:", fsa, province_code, name, file=sys.stderr)
            if not val:
                print("missing", var + ":", fsa, province_code, name, file=sys.stderr)

        # https://en.wikipedia.org/wiki/List_of_extreme_points_of_Canada
        # converted to decimal with https://www.fcc.gov/media/radio/dms-decimal
        longt, lat = float(longt), float(lat)
        if not (41.681389 <= lat <= 83.111389):
            print(f"out of bounds latitude {lat}:", fsa, province_code, name, file=sys.stderr)
        if not (-141.001944 <= longt <= -52.619444):
            print(f"out of bounds longitude {longt}:", fsa, province_code, name, file=sys.stderr)

        if not accuracy:
            print("missing accuracy:", fsa, province_code, name, file=sys.stderr)
            accuracy = None
        else:
            accuracy = int(accuracy)
            if accuracy not in range(1, 7):
                print(f"invalid accuracy {accuracy}:", fsa, province_code, name, file=sys.stderr)
                # accuracy = None

        c.execute(
            "INSERT INTO FSACodes values(?,?,?,?,?,?)",
            (fsa, name, province, lat, longt, accuracy),
        )

conn.commit()

# We can also close the cursor if we are done with it
c.close()

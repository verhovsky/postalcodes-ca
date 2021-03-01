import sqlite3
import os
import csv
import sys

try:
    from settings import db_location
except:
    from postalcodes_ca.settings import db_location

FSA_FILE = "CA.tsv"
POSTAL_CODES_FILE = "CA_full.txt"


def log_error(msg, row, row_idx=None):
    if row_idx is None:
        msg = f"{msg}: {row!r}"
    else:
        msg = f"{msg}: row {row_idx: <6} {row!r}"
    print(msg, file=sys.stderr)

def read_codes(filename):
    codes = {}
    with open(filename, newline="", encoding="utf-8") as f:
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

            # TODO: use administrative subdivisions in FSA data.
            # The 3rd level is used in Quebec.
            # For the other provinces, the second level usually holds just the city/town
            # name. The "code" for those is some 7 digit number I've never seen before.
            #
            # Unlike the FSA data, for postal codes "province_code" is a number "01"
            # for Albera, etc. You can see all of them with
            # xsv select 4,5 -d'\t' CA_full.txt  | sort | uniq
            # The admininstrative divisions (the 4 ignored fields) are always empty,
            # which you can verify with
            # xsv select 6,7,8,9 -d'\t' CA_full.txt  | sort | uniq
            country_code, code, name, province, province_code, _, _, _, _, lat, longt, accuracy, = row

            if country_code != "CA":
                log_error(f"country code {country_code!r} isn't 'CA'", row, idx)
                sys.exit(1)

            expected_len = 3 if filename == FSA_FILE else 7
            if len(code) > expected_len:
                log_error(f"code is too long  {code!r}", row, idx)
                continue
            if len(code) < expected_len:
                log_error(f"code is too short {code!r}", row, idx)
                continue

            for var, val in [("code", code), ("name", name), ("province", province), ("province_code", province_code), ("lat", lat), ("longt", longt)]:
                if val != val.strip():
                    log_error(f"{var} contains whitespace", row, idx)
                if not val:
                    log_error(f"missing {var}", row, idx)

            # TODO: report and fix this upstream
            if "Notre-Dame-de-GrÔce" in name:
                new_name = name.replace("Notre-Dame-de-GrÔce", "Notre-Dame-de-Grâce")
                log_error(f"bad name {name!r}, changing to {new_name!r}", row, idx)
                name = new_name

            # https://en.wikipedia.org/wiki/List_of_extreme_points_of_Canada
            # converted to decimal with https://www.fcc.gov/media/radio/dms-decimal
            # TODO: check that coords are in the FSA using the census shapefile
            lat, longt = float(lat), float(longt)
            if not (41.681389 <= lat <= 83.111389):
                log_error(f"out of bounds latitude {lat} {longt}", row, idx)
            if not (-141.001944 <= longt <= -52.619444):
                log_error(f"out of bounds longitude {lat} {longt}", row, idx)

            if not accuracy:
                log_error("missing accuracy", row, idx)
                accuracy = None
            else:
                accuracy = int(accuracy)
                if accuracy not in range(1, 7):
                    log_error(f"invalid accuracy {accuracy}", row, idx)
                    # accuracy = None
            if filename == POSTAL_CODES_FILE:
                if accuracy != 6:
                    log_error("accuracy for postal codes must be '6'", row, idx)

            if code in codes:
                diff_vals = sum(orig != dup for dup, orig in zip((code, name, province, lat, longt, accuracy), codes[code]))
                if diff_vals:
                    log_error(f'duplicate with {diff_vals} different value(s) {codes[code]!r}', row, idx)
                    # sys.exit(1)
            else:
                codes[code] = (code, name, province, lat, longt, accuracy)
    return codes.values()

os.remove(db_location)
conn = sqlite3.connect(db_location)
c = conn.cursor()
c.execute("DROP TABLE IF EXISTS FSACodes;")
c.execute("""\
CREATE TABLE FSACodes(
    code VARCHAR(3) NOT NULL,
    name VARCHAR(180) NOT NULL,
    province VARCHAR(100) NOT NULL,
    -- province_code VARCHAR(2) NOT NULL,
    latitude DOUBLE NOT NULL,
    longitude DOUBLE NOT NULL,
    accuracy INT
);""")
c.execute("CREATE INDEX fsa_code_index ON FSACodes(code);")
c.execute("CREATE INDEX fsa_name_index ON FSACodes(name);")
c.execute("CREATE INDEX fsa_province_index ON FSACodes(province);")

for row in read_codes(FSA_FILE):
    c.execute("INSERT INTO FSACodes values(?,?,?,?,?,?)", row)

c.execute("DROP TABLE IF EXISTS PostalCodes;")
c.execute("""\
CREATE TABLE PostalCodes(
    code VARCHAR(7) NOT NULL,
    name VARCHAR(180) NOT NULL,
    province VARCHAR(100) NOT NULL,
    latitude DOUBLE NOT NULL,
    longitude DOUBLE NOT NULL
);""")
# These indeces double the file size of postalcodes.db
c.execute("CREATE INDEX postal_code_index ON PostalCodes(code);")
c.execute("CREATE INDEX postal_name_index ON PostalCodes(name);")
c.execute("CREATE INDEX postal_province_index ON PostalCodes(province);")

postal_codes = read_codes(POSTAL_CODES_FILE)
# Santa's postal code is missing from the postal codes but not from the FSA codes
SANTA = ('H0H 0H0', 'Reserved (Santa Claus)', 'Quebec', 90, 0, 6)
for postal_code in list(postal_codes) + [SANTA]:
    # don't include accuracy, it's always 6
    c.execute("INSERT INTO PostalCodes values(?,?,?,?,?)", postal_code[:-1])

conn.commit()
c.close()

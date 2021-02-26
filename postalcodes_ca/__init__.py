from dataclasses import dataclass
import sqlite3
import string
import re
import time
from collections import namedtuple
from math import degrees, sin, asin, cos, radians

from .settings import db_location


class ConnectionManager:
    """
    Assumes a database that will work with cursor objects
    """

    def __init__(self):
        # test out the connection...
        conn = sqlite3.connect(db_location)
        conn.close()

    def query(self, sql, args=()):
        conn = None
        # If there is trouble reading the file, try 10 times then just give up...
        for retry_count in range(10):
            try:
                conn = sqlite3.connect(db_location)
                break
            except sqlite3.OperationalError:
                time.sleep(0.001)
        else:
            raise sqlite3.OperationalError("Can't connect to sqlite database at " + str(db_location))

        cursor = conn.cursor()
        cursor.execute(sql, args)
        res = cursor.fetchall()
        conn.close()
        return res

PC_QUERY = "SELECT * FROM FSACodes WHERE fsa=?"
PC_RANGE_QUERY = "SELECT * FROM FSACodes WHERE longitude >= ? and longitude <= ? AND latitude >= ? and latitude <= ?"
PC_FIND_QUERY = "SELECT * FROM FSACodes WHERE fsa LIKE ? AND name LIKE ? AND province LIKE ?"

POSTAL_CODE_ALPHABET = 'ABCEGHJKLMNPRSTVWXYZ'  # postal codes don't use D, F, I, O, Q or U
POSTAL_CODE_FIRST_LETTER_ALPHABET = 'ABCEGHJKLMNPRSTVXY'  # additionally, the first letter doesn't use W or Z


@dataclass
class FSACode:
    """The first 3 characters of a postal code"""
    fsa: str
    name: str
    province: str
    latitude: float
    longitude: float
    accuracy: int

    @property
    def is_valid(self):
        try:
            validate_fsa(self.fsa)
            return True
        except ValueError:
            return False

def format_result(codes):
    if codes:
        return [FSACode(*code) for code in codes]
    return None

def validate_fsa(fsa, strict=False):
    if not strict:
        fsa = fsa.upper()

    if len(fsa) < 3:
        raise ValueError(f"invalid FSA, must be 3 characters: {str(fsa)!r}")
    if strict and len(fsa) > 3:
        raise ValueError(f"invalid FSA, must be 3 characters: {str(fsa)!r}")

    if fsa[0] not in POSTAL_CODE_FIRST_LETTER_ALPHABET:
        raise ValueError(f"invalid FSA, must start with one of {POSTAL_CODE_FIRST_LETTER_ALPHABET}: {str(fsa)!r}")
    if fsa[1] not in string.digits:
        raise ValueError(f"invalid FSA, second character must be a digit: {str(fsa)!r}")
    if fsa[2] not in POSTAL_CODE_ALPHABET:
        raise ValueError(f"invalid FSA, third character must be one of {POSTAL_CODE_ALPHABET}: {str(fsa)!r}")

    return fsa[:3]

class CodeNotFoundException(Exception):
    pass

class FSACodeNotFoundException(CodeNotFoundException):
    pass

class FSACodeDatabase:
    def __init__(self, conn_manager=None):
        if conn_manager is None:
            conn_manager = ConnectionManager()
        self.conn_manager = conn_manager

    def get_nearby(self, fc, radius):
        # TODO: this is a square, not a radius.
        # use this: https://stackoverflow.com/a/39298241
        fc = self.get(fc)
        if fc is None:
            raise FSACodeNotFoundException("Could not find FSA code " + str(fc))

        radius = float(radius)

        '''
        Bounding box calculations updated from pyzipcode
        '''
        earth_radius  = 6371
        dlat = radius / earth_radius
        dlon = asin(sin(dlat) / cos(radians(fc.latitude)))
        lat_delta = degrees(dlat)
        lon_delta = degrees(dlon)

        if lat_delta < 0:
            lat_range = (fc.latitude + lat_delta, fc.latitude - lat_delta)
        else:
            lat_range = (fc.latitude - lat_delta, fc.latitude + lat_delta)

        long_range  = (fc.longitude - lat_delta, fc.longitude + lon_delta)

        return format_result(self.conn_manager.query(PC_RANGE_QUERY , (
            long_range[0], long_range[1],
            lat_range[0], lat_range[1]
        )))

    def search(self, fsa=None, name=None, province=None):
        if fsa is None:
            fsa = "%"
        else:
            # TODO: validate?
            fsa = fsa.upper()

        if name is None:
            name = "%"
        else:
            name = name.upper()

        if province is None:
            province = "%"
        else:
            province = province.upper()

        return format_result(self.conn_manager.query(PC_FIND_QUERY , (fsa, name, province)))

    def get(self, fc, default=None, strict=True):
        if isinstance(fc, FSACode):
            fc = fc.fsa
        if not isinstance(fc, str):
            raise TypeError('expected string, got "{type(fc)}"')
        fc = validate_fsa(fc, strict)
        results = format_result(self.conn_manager.query(PC_QUERY , (fc,)))

        if len(results) > 1:
            raise ValueError(f"looking up {fc!r} returned {len(results)} results")
        if results:
            return results[0]
        return default

    def __getitem__(self, fc):
        res = self.get(fc)
        if res is None:
            raise KeyError(fc)
        return res

fsa_codes = FSACodeDatabase()

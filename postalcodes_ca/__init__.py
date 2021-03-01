from dataclasses import dataclass
import sqlite3
import string
import re
import time
from collections import namedtuple
from collections.abc import Mapping
from math import degrees, sin, asin, cos, radians

from .settings import db_location


def parse_fsa(fsa, strict=False):
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

def parse_postal_code(pc, strict=False):
    if not strict:
        pc = pc.upper()

    if strict:
        if len(pc) != 7:
            raise ValueError(f"invalid postal code, must be 7 characters: {str(pc)!r}")
    else:
        if len(pc) < 6:
            raise ValueError(f"invalid postal code, too short: {str(pc)!r}")
        if ' ' in pc[:7] and len(pc) < 7:
            raise ValueError(f"invalid postal code, too short: {str(pc)!r}")

    try:
        fsa = parse_fsa(pc[:3], strict=strict)
    except ValueError as fsa_error:
        raise ValueError(f"invalid postal code, " + str(fsa_error))

    if strict and pc[3] != ' ':
        raise ValueError(f"invalid postal code, must include a space: {str(pc)!r}")

    ldu = pc[4:7] if pc[3] == ' ' else pc[3:6]

    if ldu[0] not in string.digits:
        raise ValueError(f"invalid postal code, fourth character must be a digit: {str(pc)!r}")
    if ldu[1] not in POSTAL_CODE_ALPHABET:
        raise ValueError(f"invalid postal code, fifth character must be one of {POSTAL_CODE_ALPHABET}: {str(pc)!r}")
    if ldu[2] not in string.digits:
        raise ValueError(f"invalid postal code, sixth character must be a digit: {str(pc)!r}")

    return fsa + ' ' + ldu


@dataclass
class Code:
    """A base class used for postal codes and FSA codes"""
    code: str
    name: str
    province: str
    latitude: float
    longitude: float

    def _parse(self, fsa):
        raise NotImplementedError

    @property
    def is_valid(self):
        try:
            self._parse(self.fsa)
            return True
        except ValueError:
            return False

    @property
    def postal_district(self):
        return self.code[0]

    @property
    def fsa(self):
        return self.code[:3]

    @property
    def is_rural(self):
        # TODO: are there any exceptions?
        return self.code[1] == "0"

@dataclass
class FSA(Code):
    """The first 3 characters of a Canadian postal code"""
    accuracy: int

    _parse = parse_fsa

@dataclass
class PostalCode(Code):
    """A 6 character Canadian postal code"""
    _parse = parse_postal_code

    @property
    def accuracy(self):
        return 6



class ConnectionManager:
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

QUERY = "SELECT * FROM {table_name} WHERE code=?"
RANGE_QUERY = "SELECT * FROM {table_name} WHERE longitude >= ? and longitude <= ? AND latitude >= ? and latitude <= ?"
FIND_QUERY = "SELECT * FROM {table_name} WHERE code LIKE ? AND name LIKE ? AND province LIKE ?"
ALL_QUERY = "SELECT * FROM {table_name}"
LEN_QUERY = "SELECT COUNT(*) FROM {table_name}"

POSTAL_CODE_ALPHABET = 'ABCEGHJKLMNPRSTVWXYZ'  # postal codes don't use D, F, I, O, Q or U
POSTAL_CODE_FIRST_LETTER_ALPHABET = 'ABCEGHJKLMNPRSTVXY'  # additionally, the first letter doesn't use W or Z

# TODO: check if using sets for the above improves performance


class CodeNotFoundException(Exception):
    pass

class FSANotFoundException(CodeNotFoundException):
    pass

class PostalCodeNotFoundException(CodeNotFoundException):
    pass

class CodeDatabase(Mapping):
    result_type = Code
    not_found_exception = CodeNotFoundException
    parse = lambda x: x

    def __init__(self, conn_manager=None):
        if conn_manager is None:
            conn_manager = ConnectionManager()
        self.conn_manager = conn_manager

    def _format_result(self, codes):
        if codes:
            return [self.result_type(*code) for code in codes]
        return None

    def get_nearby(self, code, radius):
        # TODO: this is a square, not a radius.
        # use this: https://stackoverflow.com/a/39298241
        code = self.get(code)
        if code is None:
            raise self.not_found_exception("Could not find code " + str(code))

        radius = float(radius)

        '''
        Bounding box calculations updated from pyzipcode
        '''
        earth_radius  = 6371
        dlat = radius / earth_radius
        dlon = asin(sin(dlat) / cos(radians(code.latitude)))
        lat_delta = degrees(dlat)
        lon_delta = degrees(dlon)

        if lat_delta < 0:
            lat_range = (code.latitude + lat_delta, code.latitude - lat_delta)
        else:
            lat_range = (code.latitude - lat_delta, code.latitude + lat_delta)

        long_range  = (code.longitude - lat_delta, code.longitude + lon_delta)

        # TODO: return empty list instead of None?
        return self._format_result(self.conn_manager.query(self.RANGE_QUERY, (
            long_range[0], long_range[1],
            lat_range[0], lat_range[1]
        )))

    def search(self, code=None, name=None, province=None):
        # TODO: allow passing an FSA/PostalCode object?
        if code is None:
            code = "%"
        else:
            # TODO: validate?
            code = code.upper()

        if name is None:
            name = "%"
        else:
            name = name.upper()

        if province is None:
            province = "%"
        else:
            province = province.upper()

        # TODO: return empty list instead of None?
        return self._format_result(self.conn_manager.query(self.FIND_QUERY , (code, name, province)))

    def get(self, code, default=None, strict=True):
        if isinstance(code, self.result_type):
            code = code.code
        if not isinstance(code, str):
            raise TypeError('expected string or {self.result_type}, got "{type(code)}"')
        code = self.parse(code, strict)
        results = self._format_result(self.conn_manager.query(self.QUERY, (code,)))
        if results is None:
            return default
        if len(results) > 1:
            raise ValueError(f"looking up {code!r} returned {len(results)} results")
        return results[0]

    def __getitem__(self, code):
        res = self.get(code)
        if res is None:
            raise KeyError(code)
        return res

    def __iter__(self):
        results = self.conn_manager.query(self.ALL_QUERY)
        for res in results:
            yield self.result_type(*res)

    def __len__(self):
        return self.conn_manager.query(self.LEN_QUERY)[0][0]


class FSADatabase(CodeDatabase):
    result_type = FSA
    not_found_exception = FSANotFoundException

    def parse(self, *args, **kwargs):
        return parse_fsa(*args, **kwargs)

    QUERY = QUERY.format(table_name="FSACodes")
    RANGE_QUERY = RANGE_QUERY.format(table_name="FSACodes")
    FIND_QUERY = FIND_QUERY.format(table_name="FSACodes")
    ALL_QUERY = ALL_QUERY.format(table_name="FSACodes")
    LEN_QUERY = LEN_QUERY.format(table_name="FSACodes")


class PostalCodeDatabase(CodeDatabase):
    result_type = PostalCode
    not_found_exception = PostalCodeNotFoundException

    def parse(self, *args, **kwargs):
        return parse_postal_code(*args, **kwargs)

    QUERY = QUERY.format(table_name="PostalCodes")
    RANGE_QUERY = RANGE_QUERY.format(table_name="PostalCodes")
    FIND_QUERY = FIND_QUERY.format(table_name="PostalCodes")
    ALL_QUERY = ALL_QUERY.format(table_name="PostalCodes")
    LEN_QUERY = LEN_QUERY.format(table_name="PostalCodes")


fsa_codes = FSADatabase()
postal_codes = PostalCodeDatabase()

# TODO: unified database that can return either?
# codes = CodesDatabase()

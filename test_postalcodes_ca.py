import itertools
from collections import Counter
from string import digits, ascii_uppercase

import pytest

from postalcodes_ca import postal_codes, fsa_codes
from postalcodes_ca import PostalCode, FSA
from postalcodes_ca import parse_postal_code, parse_fsa
from postalcodes_ca import POSTAL_CODE_ALPHABET, POSTAL_CODE_FIRST_LETTER_ALPHABET


def test_get():
    res = fsa_codes.get("T2S")
    assert isinstance(res, FSA)
    res = postal_codes.get("M5V 3L9")
    assert isinstance(res, PostalCode)


def test_parse_postal_code():
    assert parse_postal_code("M5V 3L9") == "M5V 3L9"


def test_parse_fsa():
    with pytest.raises(ValueError):
        fsa_codes.get("T2O")
    with pytest.raises(ValueError):
        fsa_codes.get("t2s")
    with pytest.raises(ValueError):
        fsa_codes.get("t2s ")
    with pytest.raises(ValueError):
        fsa_codes.get("")
    with pytest.raises(ValueError):
        fsa_codes.get("Z2S")
    with pytest.raises(ValueError):
        fsa_codes.get("T2", strict=False)

    for fsa in itertools.product(
        POSTAL_CODE_FIRST_LETTER_ALPHABET, digits, POSTAL_CODE_ALPHABET
    ):
        parse_fsa("".join(fsa))

    invalid_first_letter = set(ascii_uppercase) - set(POSTAL_CODE_FIRST_LETTER_ALPHABET)
    for fsa in itertools.product(invalid_first_letter, digits, ascii_uppercase):
        fsa = "".join(fsa)
        with pytest.raises(ValueError):
            parse_fsa(fsa)

    invalid_second_letter = set(ascii_uppercase) - set(POSTAL_CODE_ALPHABET)
    for fsa in itertools.product(ascii_uppercase, digits, invalid_second_letter):
        fsa = "".join(fsa)
        with pytest.raises(ValueError):
            parse_fsa(fsa)


def test_parse_postal_code_not_strict():
    assert parse_postal_code("M5V 3L9", strict=False) == "M5V 3L9"
    assert parse_postal_code("m5v 3L9", strict=False) == "M5V 3L9"
    assert parse_postal_code("m5V3L9", strict=False) == "M5V 3L9"
    assert parse_postal_code("m5V3L9aaaaa", strict=False) == "M5V 3L9"
    with pytest.raises(ValueError):
        parse_postal_code("M5V    ", strict=False)
    with pytest.raises(ValueError):
        parse_postal_code("Z5V3L9", strict=False)
    assert parse_postal_code("M5V3L9       ", strict=False) == "M5V 3L9"
    assert parse_postal_code("M5V3L9 ", strict=False) == "M5V 3L9"
    with pytest.raises(ValueError):
        parse_postal_code("M5V3L ", strict=False)


def test_parse_fsa_not_strict():
    with pytest.raises(ValueError):
        fsa_codes.get("T2O", strict=False)
    fsa_codes.get("t2s", strict=False)
    fsa_codes.get("t2s ", strict=False)
    fsa_codes.get("t2S ", strict=False)
    with pytest.raises(ValueError):
        fsa_codes.get("", strict=False)
    with pytest.raises(ValueError):
        fsa_codes.get("Z2S", strict=False)
    with pytest.raises(ValueError):
        fsa_codes.get("T2", strict=False)

    for fsa in itertools.product(
        POSTAL_CODE_FIRST_LETTER_ALPHABET, digits, POSTAL_CODE_ALPHABET
    ):
        parse_fsa("".join(fsa), strict=False)

    # TODO: should strict=False accept any letter?
    invalid_first_letter = set(ascii_uppercase) - set(POSTAL_CODE_FIRST_LETTER_ALPHABET)
    for fsa in itertools.product(invalid_first_letter, digits, ascii_uppercase):
        fsa = "".join(fsa)
        with pytest.raises(ValueError):
            parse_fsa(fsa, strict=False)

    invalid_second_letter = set(ascii_uppercase) - set(POSTAL_CODE_ALPHABET)
    for fsa in itertools.product(ascii_uppercase, digits, invalid_second_letter):
        fsa = "".join(fsa)
        with pytest.raises(ValueError):
            parse_fsa(fsa, strict=False)


def test_get_not_strict():
    res = fsa_codes.get("t2s", strict=False)
    assert isinstance(res, FSA)


def test_get_types():
    postal_code = postal_codes["M5V 3L9"]
    fsa = fsa_codes["M5V"]
    with pytest.raises(TypeError):
        postal_codes[fsa]
    with pytest.raises(TypeError):
        fsa_codes[postal_code]
    fsa_codes[fsa.code] == fsa
    postal_codes[postal_code.code] == postal_code


def test_search_types():
    postal_code = postal_codes["M5V 3L9"]
    fsa = fsa_codes["M5V"]
    with pytest.raises(AttributeError):
        fsa_codes.search(code=postal_code)
    with pytest.raises(AttributeError):
        fsa_codes.search(code=fsa)
    with pytest.raises(AttributeError):
        postal_codes.search(code=postal_code)
    with pytest.raises(AttributeError):
        postal_codes.search(code=fsa)


def test_key_lookup_and_get_nearby():
    code = "T2S"
    fsa = fsa_codes[code]
    assert isinstance(fsa, FSA)
    radius = 5  # km
    res = fsa_codes.get_nearby(fsa, radius)
    # TODO: don't return the original fsa in the results?
    assert len(res) == 7
    assert fsa in res

    with pytest.raises(KeyError):
        fsa_codes["A9X"]
    with pytest.raises(KeyError):
        postal_codes["A9X 6T9"]


def test_accuracy_can_be_none():
    fsa = fsa_codes["T2S"]
    assert isinstance(fsa.accuracy, int)
    # There are a dozen postal codes without an accuracy,
    # the one for the North Pole should never have an accuracy
    fsa = fsa_codes["H0H"]
    assert fsa.accuracy is None


def test_search():
    expected_result_count = 20  # this could change

    res = fsa_codes.search(code="T2%")
    assert len(res) <= len(POSTAL_CODE_ALPHABET)
    assert len(res) == expected_result_count

    res = fsa_codes.search(code="T2%", name="Calgary%")
    assert len(res) == expected_result_count

    res = fsa_codes.search(code="T%", name="Toronto%")
    assert res is None


@pytest.mark.skip(".values() and .items() take minutes to run")
def test_data():
    province_names = []
    for code_obj in fsa_codes.values():
        province_names.append(code_obj.province)
    assert len(set(province_names)) == 13

    # check that postal codes and FSAs use the same province names
    for code_obj in postal_codes.values():
        province_names.append(code_obj.province)
    assert len(set(province_names)) == 13
    del province_names

    # check that codes are unique
    print(Counter(p.code for p in postal_codes.values()).most_common(1000))
    assert Counter(p.code for p in postal_codes.values()).most_common()[0][1] == 1
    print(Counter(p.code for p in fsa_codes.values()).most_common(20))
    assert Counter(p.code for p in fsa_codes.values()).most_common()[0][1] == 1


def test_len_and_iter():
    assert len(postal_codes) > 800_000
    assert len(list(postal_codes)) == len(postal_codes)

    assert len(fsa_codes) > 1600
    assert len(list(fsa_codes)) == len(fsa_codes)

from postalcodes_ca import fsa_codes, FSACode, validate_fsa, POSTAL_CODE_ALPHABET, POSTAL_CODE_FIRST_LETTER_ALPHABET
from string import digits, ascii_uppercase
import itertools
import pytest

def test_get():
    res = fsa_codes.get("T2S")
    assert isinstance(res, FSACode)

def test_validate():
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

    for fsa in itertools.product(POSTAL_CODE_FIRST_LETTER_ALPHABET, digits, POSTAL_CODE_ALPHABET):
        validate_fsa(''.join(fsa))

    invalid_first_letter = set(ascii_uppercase) - set(POSTAL_CODE_FIRST_LETTER_ALPHABET)
    for fsa in itertools.product(invalid_first_letter, digits, ascii_uppercase):
        fsa = ''.join(fsa)
        with pytest.raises(ValueError):
            validate_fsa(fsa)

    invalid_second_letter = set(ascii_uppercase) - set(POSTAL_CODE_ALPHABET)
    for fsa in itertools.product(ascii_uppercase, digits, invalid_second_letter):
        fsa = ''.join(fsa)
        with pytest.raises(ValueError):
            validate_fsa(fsa)

def test_validate_not_strict():
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

    for fsa in itertools.product(POSTAL_CODE_FIRST_LETTER_ALPHABET, digits, POSTAL_CODE_ALPHABET):
        validate_fsa(''.join(fsa), strict=False)

    # TODO: should strict=False accept any letter?
    invalid_first_letter = set(ascii_uppercase) - set(POSTAL_CODE_FIRST_LETTER_ALPHABET)
    for fsa in itertools.product(invalid_first_letter, digits, ascii_uppercase):
        fsa = ''.join(fsa)
        with pytest.raises(ValueError):
            validate_fsa(fsa, strict=False)

    invalid_second_letter = set(ascii_uppercase) - set(POSTAL_CODE_ALPHABET)
    for fsa in itertools.product(ascii_uppercase, digits, invalid_second_letter):
        fsa = ''.join(fsa)
        with pytest.raises(ValueError):
            validate_fsa(fsa, strict=False)


def test_get_not_strict():
    res = fsa_codes.get("t2s", strict=False)
    assert isinstance(res, FSACode)

def test_key_lookup_and_get_nearby():
    code = "T2S"
    fsa = fsa_codes[code]
    assert isinstance(fsa, FSACode)
    radius = 5  # km
    res = fsa_codes.get_nearby(fsa, radius)
    # TODO: don't return the original fsa in the results?
    assert len(res) == 7
    assert fsa in res

def test_accuracy_can_be_none():
    fsa = fsa_codes["T2S"]
    assert isinstance(fsa.accuracy, int)
    # There are a dozen postal codes without an accuracy,
    # the one for the North Pole should never have an accuracy
    fsa = fsa_codes["H0H"]
    assert fsa.accuracy is None

def test_search():
    res = fsa_codes.search(fsa="T2%")

    expected_result_count = 20  # this might change
    assert len(res) <= len(POSTAL_CODE_ALPHABET)
    assert len(res) == expected_result_count

    res = fsa_codes.search(fsa="T%", name="Toronto%")
    assert res is None

    res = fsa_codes.search(fsa="T2%", name="Calgary%")
    assert len(res) == expected_result_count

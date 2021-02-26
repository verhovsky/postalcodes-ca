# postalcodes-ca

This is a fork of Scott Rodkey's [`pypostalcode`](https://pypi.org/project/pypostalcode/) package, which is itself a fork of Nathan Van Gheem's [`pyzipcode`](https://pypi.org/project/pyzipcode/) package. The zipcode database has been replaced with Canadian cities and their postal codes. The general usage is similar.

## Primer on Canadian postal codes

[Canadian postal codes](https://en.wikipedia.org/wiki/Postal_codes_in_Canada) are six characters in this format:

`A1A 1A1`

where `A` is a letter and `1` is a digit, with a space separating the third and fourth characters. The first three digits are the **Forward Sortation Area** (**FSA**), and the last three are the **Local Delivery Unit** (**LDU**). 

This module only supports looking up FSA codes. There are over 878,000 FSA+LDU combinations, but the 1,655 (+1 for Santa) unique FSA values provide coarse resolution for most applications.

Read the [Postal codes in Canada](https://en.wikipedia.org/wiki/Postal_codes_in_Canada) article on Wikipedia for more information.

The data is from [GeoNames](https://www.geonames.org/) https://download.geonames.org/export/zip/ which is distributed under a [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) license. Please respect the license if you use this module.

## Install

To install:

```
pip install postalcodes-ca
```


## Usage

```pycon
>>> from postalcodes_ca import fsa_codes
>>> fsa_codes['V5K']
FSACode(fsa='V5K', name='Vancouver (North Hastings-Sunrise)', province='British Columbia', latitude=49.2807, longitude=-123.0397, accuracy=6)
>>> fsa_codes.get('V5K')
FSACode(fsa='V5K', name='Vancouver (North Hastings-Sunrise)', province='British Columbia', latitude=49.2807, longitude=-123.0397, accuracy=6)
>>> fsa_codes.get('v5k')
[...]
ValueError: invalid FSA, must start with one of ABCEGHJKLMNPRSTVXY: 'v5k'
>>> fsa_codes.get('v5kblahblah', strict=False)  # only the first 3 characters are used
FSACode(fsa='V5K', name='Vancouver (North Hastings-Sunrise)', province='British Columbia', latitude=49.2807, longitude=-123.0397, accuracy=6)
```

Get a list of postal codes given a radius in kilometers 

```pycon
>>> results = fsa_codes.get_nearby('V5K', radius=4)
>>> for r in results:
...     print(f"{r.fsa}: {r.name}, {r.province}")
... 
V5K: Vancouver (North Hastings-Sunrise), British Columbia
V5L: Vancouver (North Grandview-Woodlands), British Columbia
V5M: Vancouver (South Hastings-Sunrise / North Renfrew-Collingwood), British Columbia
V5N: Vancouver (South Grandview-Woodlands / NE Kensington), British Columbia
V7L: North Vancouver South Central, British Columbia
V5C: Burnaby (Burnaby Heights / Willingdon Heights / West Central Valley), British Columbia
V5G: Burnaby (Cascade-Schou / Douglas-Gilpin), British Columbia
```

if you have miles, multiply by `1.609344`. Note that this actually searches a square area, not a circle with a radius.

Search by FSA code, city name or province name:

``` pycon
>>> fsa_codes.search(name='Calgary')
[FSACode(fsa='T3S', name='Calgary', province='Alberta', latitude=50.9153, longitude=-113.8932, accuracy=4)]
>>> len(fsa_codes.search(name='Calgary%'))
35
>>> len(fsa_codes.search(fsa='T2%'))
20
>>> len(fsa_codes.search(province='Alberta'))
154
>>> fsa_codes.search(province='California')  # returns None
>>>
```

### Notes

There is the special Postal Code for Santa (who lives at the North Pole), `H0H 0H0`, which looks like this:

``` python
>>> fsa_codes['H0H']
FSACode(fsa='H0H', name='Reserved (Santa Claus)', province='Quebec', latitude=90.0, longitude=0.0, accuracy=None)
```

## Development

### How to contribute to the data

If you notice an issue with the data, you can report it by creating a GitHub account and
[creating a new issue](https://github.com/verhovsky/postalcodes-ca/issues/new).

If you want to fix the issue yourself, then look at
[`CA.tsv`](https://github.com/verhovsky/postalcodes-ca/blob/master/CA.tsv),
figure out what needs to be changed and report the issue to the GeoNames
project. Once it is fixed upstream you can create an issue on `postalcodes-ca`
to tell us to update the data.

### How to update the vendored data

0) `cd` into the same directory as this readme file
1) go to https://download.geonames.org/export/zip/
2) download click on `CA.zip` (not `CA_full.csv.zip`)
3) unzip the file into this directory with `unzip CA.zip CA.txt`
4) compare the file you just downloaded with the that's already used with `diff CA.tsv CA.txt`. If that command produces no output, there's nothing more to do
5) rename `CA.txt` to `CA.tsv` with `mv CA.txt CA.tsv` (we rename the file so that it renders nicely on GitHub)
6) run `python3 postalcodes-ca/import.py` to update `postalcodes-ca/postalcodes.db` file

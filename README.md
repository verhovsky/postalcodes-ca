# postalcodes-ca

[`postalcodes-ca`](https://pypi.org/project/postalcodes-ca/) is a fork of Scott Rodkey's [`pypostalcode`](https://pypi.org/project/pypostalcode/) package, which is itself a fork of Nathan Van Gheem's [`pyzipcode`](https://pypi.org/project/pyzipcode/) package. The zipcode database has been replaced with Canadian cities and their postal codes. The general usage is similar.

## Install

To install:

```
pip install postalcodes-ca
```

## `A1A 1A1` - a primer on Canadian postal codes

[Canadian postal codes](https://en.wikipedia.org/wiki/Postal_codes_in_Canada) are six characters in the format `A1A 1A1`, where `A` is a letter and `1` is a digit, with a space separating the third and fourth characters. Postal codes do not use the 6 letters D, F, I, O, Q or U. Additionally, W and Z are not used as the first letter of any postal code. 

The first three characters are the **forward sortation area** (**FSA**), and the last three are the **local delivery unit** (**LDU**). The first letter, called the **postal district**, tells you the province. Quebec and Ontario have multiple postal districts and `X` is used for both Nunavut and the Northwest Territories. The second character (a digit) tells you if the postal code is [urban](https://en.wikipedia.org/wiki/Urban_area) or [rural](https://en.wikipedia.org/wiki/Rural_area), a `0` (e.g. [`A0A`](https://en.wikipedia.org/wiki/List_of_postal_codes_of_Canada:_A)) means it's rural, any other number means it's urban. See [Postal codes in Canada](https://en.wikipedia.org/wiki/Postal_codes_in_Canada) on Wikipedia for details.

This module supports looking up both full postal codes and FSA codes. There are 1,651 (+1 for Santa) FSA codes and 877,409 (+1 for Santa) FSA+LDU combinations (out of a maximum possible 18\*10\*20 = 3,600 FSA codes and 18\*10\*20\*10\*20\*10 = 7,200,000 postal codes).

## Usage

```pycon
>>> from postalcodes_ca import fsa_codes
>>> fsa_codes['V5K']
FSA(code='V5K', name='Vancouver (North Hastings-Sunrise)', province='British Columbia', latitude=49.2807, longitude=-123.0397, accuracy=6)
>>> fsa_codes.get('V5K')
FSA(code='V5K', name='Vancouver (North Hastings-Sunrise)', province='British Columbia', latitude=49.2807, longitude=-123.0397, accuracy=6)
>>> fsa_codes.get('v5k')
[...]
ValueError: invalid FSA, must start with one of ABCEGHJKLMNPRSTVXY: 'v5k'
>>> fsa_codes.get('v5kblahblah', strict=False)  # only the first 3 characters are used
FSA(code='V5K', name='Vancouver (North Hastings-Sunrise)', province='British Columbia', latitude=49.2807, longitude=-123.0397, accuracy=6)
```

Get a list of FSA codes given a radius in kilometers (multiply by `1.609344` if you have miles). Note that this actually searches a square area, not a circle with a radius:

```pycon
>>> results = fsa_codes.get_nearby('V5K', radius=4)
>>> for r in results:
...     print(f"{r.code}: {r.name}, {r.province}")
... 
V5K: Vancouver (North Hastings-Sunrise), British Columbia
V5L: Vancouver (North Grandview-Woodlands), British Columbia
V5M: Vancouver (South Hastings-Sunrise / North Renfrew-Collingwood), British Columbia
V5N: Vancouver (South Grandview-Woodlands / NE Kensington), British Columbia
V7L: North Vancouver South Central, British Columbia
V5C: Burnaby (Burnaby Heights / Willingdon Heights / West Central Valley), British Columbia
V5G: Burnaby (Cascade-Schou / Douglas-Gilpin), British Columbia
```

Search by code, city name or province name using [SQL syntax](https://sqlite.org/lang_corefunc.html#like):

```pycon
>>> fsa_codes.search(name='Calgary')  # exact match
[FSA(code='T3S', name='Calgary', province='Alberta', latitude=50.9153, longitude=-113.8932, accuracy=4)]
>>> len(fsa_codes.search(name='Calgary%'))
35
>>> len(fsa_codes.search(code='T2%'))
20
>>> len(fsa_codes.search(province='Alberta'))
154
>>> fsa_codes.search(province='California')  # returns None
>>> 
```

There's an identical API for postal codes, but keep in mind that the data is of a lower quality (see [below](#differences-between-data-in-postal_codes-and-fsa_codes)):

```pycon
>>> from postalcodes_ca import postal_codes
>>> postal_codes['M5V 3L9']
PostalCode(code='M5V 3L9', name='Toronto', province='Ontario', latitude=43.642, longitude=-79.386)
>>> postal_codes.get('M5V 3L9')
PostalCode(code='M5V 3L9', name='Toronto', province='Ontario', latitude=43.642, longitude=-79.386)
>>> postal_codes.get('m5v3l9')
[...]
ValueError: invalid postal code, must be 7 characters: 'm5v3l9'
>>> postal_codes.get('m5v3l9blahblah', strict=False)  # only the first 6 or 7 characters are used
PostalCode(code='M5V 3L9', name='Toronto', province='Ontario', latitude=43.642, longitude=-79.386)
```

Check if a string matches the format of a postal code or FSA code:

```pycon
>>> from postalcodes_ca import parse_postal_code, parse_fsa
>>> parse_postal_code('m5v3l9 blah  ')
'M5V 3L9'
>>> parse_postal_code('m5v3l9 blah  ', strict=True)
[...]
ValueError: invalid postal code, must be 7 characters: 'm5v3l9 blah  '
>>> parse_fsa('M5V')
'M5V'
>>> parse_fsa('M5V 3L9')
'M5V'
>>> parse_fsa('M5V 3L9', strict=True)
[...]
ValueError: invalid FSA, must be 3 characters: 'M5V 3L9'
```

### Notes


#### `H0H 0H0` - Santa's postal code

There is a special postal code for Santa Claus which looks like this:

```pycon
>>> postal_codes["H0H 0H0"]
PostalCode(code='H0H 0H0', name='Reserved (Santa Claus)', province='Quebec', latitude=90.0, longitude=0.0)
>>> fsa_codes['H0H']
FSA(code='H0H', name='Reserved (Santa Claus)', province='Quebec', latitude=90.0, longitude=0.0, accuracy=None)
```

Even though Santa lives at the North Pole, the province is given as "Quebec" because `H` starts a Quebec postal code.

`postalcodes-ca` treats `H0H 0H0` like any other postal code because it's a legitimate postal code that gets a million letters each year.

#### Differences between data in `postal_codes` and `fsa_codes`

`PostalCode` names never have accents but some `FSA` names do:

```pycon
>>> fsa_codes["G4X"].name
'Gaspé'
>>> postal_codes["G4X 6T9"].name
'Gaspe'
```

`FSA` codes' names can be more descriptive

```pycon
>>> fsa_codes["V5K"].name
'Vancouver (North Hastings-Sunrise)'
>>> postal_codes["V5K 5G9"].name
'Vancouver'
```

`FSA` codes have an `accuracy` property which is either `None` or an integer between 1-6 (inclusive) representing the accuracy of their lat/lng coordinates where "`1=estimated, 4=geonameid, 6=centroid of addresses or shape`"

```pycon
>>> fsa_codes["G4X"].accuracy
4
```

About a dozen `FSA` codes have `None` as their `.accuracy`.

For `PostalCode`s, `.accuracy` is always `6`.

#### Postal code location data isn't always accurate

There are at least 92 `PostalCodes` whose latitude/longitude coordinates are completely outside Canada. I found this using basic sanity checking (see [`import.py`](https://github.com/verhovsky/postalcodes-ca/blob/master/postalcodes_ca/import.py)), which probably means that there are more datapoints which are wrong. See [this post](https://groups.google.com/g/geonames/c/wDWE29lwYho) on the GeoNames mailing list for details.

#### The data has multiple entries for some postal codes

In the original data there are 4 duplicate entries for FSA codes and 842 duplicate entries for postal codes. Usually those contain extra names for the postal code (for codes that cover multiple places) but sometimes the lat/long coordinates can be different as well. `postalcodes-ca` just uses the first code to appear in the CSV.

#### Internally reserved codes are not included

There are some FSA codes such as [`A9X`](https://en.wikipedia.org/wiki/List_of_postal_codes_of_Canada:_A) which are "reserved for internal testing", those are not in the data:

```pycon
>>> fsa_codes['A9X']
[...]
KeyError: 'A9X'
```

#### Postal codes and FSAs are not actually points

While this package associates postal codes and FSA codes to points, these codes actually represent areas, as you can see from [this map of FSA regions](https://github.com/verhovsky/postalcodes-ca/blob/master/forward_sortation_areas_2016_census.png):

![Map of Canada split into FSA postal regions as of 2016](https://raw.githubusercontent.com/verhovsky/postalcodes-ca/master/forward_sortation_areas_2016_census.png)

([data](https://www12.statcan.gc.ca/census-recensement/2011/geo/bound-limit/files-fichiers/2016/lfsa000b16a_e.zip) from [the 2016 census](https://www12.statcan.gc.ca/census-recensement/2011/geo/bound-limit/bound-limit-2016-eng.cfm) visualized using [QGIS](https://www.qgis.org/en/site/), see https://github.com/inkjet/pypostalcode/issues/6 for details)

#### Data is CC BY 4.0

https://download.geonames.org/export/zip/

The data is from [GeoNames](https://www.geonames.org/). It's distributed under a [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) license. Please respect the license if you use this module.

## Development

### How to contribute to the data

If you notice an issue with the data, you can report it by creating a GitHub account and [creating a new issue](https://github.com/verhovsky/postalcodes-ca/issues/new).

If you want to fix the issue yourself, then look at [`CA.tsv`](https://github.com/verhovsky/postalcodes-ca/blob/master/CA.tsv), figure out what needs to be changed and report the issue to the GeoNames project on [their mailing list](https://groups.google.com/g/geonames). Once it is fixed you can create an issue on `postalcodes-ca` to tell us to update the data.

### How to update the vendored data

```sh
cd postalcodes-ca/
bash update_data.sh
```

or you can do it manually:

#### `CA.tsv` - FSA codes

0) `cd` into the same directory as this readme file
1) go to https://download.geonames.org/export/zip/
2) download `CA.zip` (not `CA_full.csv.zip`)
3) unzip the file into this directory with `unzip CA.zip CA.txt`
4) compare the file you just downloaded against the one that's already used with `diff CA.tsv CA.txt`. If that command produces no output, there's nothing more to do
5) rename `CA.txt` to `CA.tsv` with `mv CA.txt CA.tsv` (we rename the file so that it renders nicely on GitHub)
6) run `python3 postalcodes-ca/import.py` to update the `postalcodes-ca/postalcodes.db` file

#### `CA_full.tsv` - postal codes

0) `cd` into the same directory as this readme file
1) go to https://download.geonames.org/export/zip/
2) download `CA_full.csv.zip` (not `CA.zip`)
3) unzip the file into this directory with `unzip CA_full.csv.zip CA_full.txt`
6) run `python3 postalcodes-ca/import.py` to update the `postalcodes-ca/postalcodes.db` file

### Package size

Just the database of FSA codes (`CA.txt`/`CA.tsv`) is negligible, the original data is 40KB zipped, 124KB unzipped and 250KB as sqlite (with indices).

The full postal codes database `CA_full.txt` (downloaded as `CA_full.csv.zip`) is 6MB zipped, 48MB unzipped. The sqlite .db file with only the 4 important fields (without indices) is 37MB. With a province field it grows to 46MB and with indices further to 95MB. When uploading to PyPI the package is zipped down to 36 MB which is below PyPI's [60MB limit](https://github.com/pypa/packaging-problems/issues/86), but this might cause issues in the future.

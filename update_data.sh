#!/usr/bin/env bash
set -euo pipefail

# Must be run from postalcodes-ca/ (the top directory, not postalcodes_ca/)

wget https://download.geonames.org/export/zip/CA.zip
unzip -o CA.zip
mv CA.txt CA.tsv

wget https://download.geonames.org/export/zip/CA_full.csv.zip
unzip -o CA_full.csv.zip

python3 postalcodes_ca/import.py

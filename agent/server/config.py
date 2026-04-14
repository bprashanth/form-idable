from pathlib import Path

# server/ root — same directory as this file
SERVER_ROOT = Path(__file__).resolve().parent

CHEATSHEET_PATH  = SERVER_ROOT / "cheatsheet.json"
SPECIES_CSV_PATH = SERVER_ROOT / "data" / "species_name.csv"

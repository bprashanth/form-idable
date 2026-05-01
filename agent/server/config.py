from pathlib import Path

# server/ root — same directory as this file
SERVER_ROOT = Path(__file__).resolve().parent

CHEATSHEET_PATH  = SERVER_ROOT / "cheatsheet.json"
SPECIES_CSV_PATH = SERVER_ROOT / "data" / "species_name.csv"

# Reserved column written by Good Shepherd into every uploaded workbook.
# Used as the stable per-row join key between Excel and image bboxes.
# Must match good-shepherd/server/services/excel_service.py exactly.
SYSTEM_SERIAL_HEADER = "(Good Shepherd) Row ID"

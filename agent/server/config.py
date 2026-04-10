from pathlib import Path

# agent/ root — one level above server/
AGENT_ROOT = Path(__file__).resolve().parents[1]

CHEATSHEET_PATH = AGENT_ROOT / "server" / "cheatsheet.json"
SPECIES_CSV_PATH = AGENT_ROOT / "data" / "species_name.csv"
SCRIPTS_DIR      = AGENT_ROOT / "scripts"
PROMPTS_DIR      = AGENT_ROOT / "prompts"

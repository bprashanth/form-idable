import json
import subprocess
import tempfile
from pathlib import Path

from config import SCRIPTS_DIR, PROMPTS_DIR, SPECIES_CSV_PATH


def _sanitize_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def propose_species_corrections(unique_values: list) -> list:
    prompt_template = (PROMPTS_DIR / "species_check.md").read_text(encoding="utf-8")
    prompt = prompt_template + json.dumps(unique_values, indent=2)

    with tempfile.TemporaryDirectory() as tmpdir:
        prompt_path = Path(tmpdir) / "prompt.md"
        prompt_path.write_text(prompt, encoding="utf-8")

        result = subprocess.run(
            [str(SCRIPTS_DIR / "run_agent.sh"), str(prompt_path), str(SPECIES_CSV_PATH)],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )

    data = json.loads(_sanitize_json(result.stdout))
    return data.get("corrections", [])

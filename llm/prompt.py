import json
from pathlib import Path


class PlainTextPrompt:
    def __init__(self, path):
        self.text = Path(path).read_text(encoding="utf-8")

    def system(self):
        return "You are an OCR-to-JSON assistant."

    def user(self):
        return self.text


class ClassifyPrompt(PlainTextPrompt):
    """Clarity wrapper for classification step."""


class IdentifyPrompt(PlainTextPrompt):
    """Clarity wrapper for identification step."""


class ExtractPrompt(PlainTextPrompt):
    """Builds the prompt for the extract step.

    Args: 
        path: Path to the prompt template.
        species_names: List of species names.
        form_instructions: Form instructions.

    Typically invoked with the output of the classify step. The classify steps 
    says here are the form types->variables mapping, and this class builds the 
    prompt for a given form type by templating those varibles into the 
    template. 

    Returns: 
        Prompt string.
    """

    def __init__(self, path, species_names=None, form_instructions=None):
        super().__init__(path)
        self.species_names = species_names or []
        self.form_instructions = form_instructions or ""

    def user(self):
        # Fill template fields if present
        return self.text.format(
            species_names=json.dumps(self.species_names, indent=2),
            form_instructions=self.form_instructions,
        )

    def build_form_instructions(self, classify_output):
        """
        Given classification JSON, construct instructions string.

        Example classify_output: 
        {
            "form_id": "plot",
            "id_variables": ["transectID", "blockID", "plotID", "date"],
            "row_represents": "one woody stem >1 cm DBH",
            "row_variables": ["species", "habit", "dbh_cm", "phenology"]
        }

        Returns: 
        "This is a PLOT form (10x10m). Each row = one woody stem >1 cm DBH. Fill only: species, habit, dbh_cm, phenology, and identifiers (transectID, blockID, plotID, date)."
        """
        ids = ", ".join(classify_output.get("id_variables", []))
        vars_ = ", ".join(classify_output.get("row_variables", []))

        return f"This is {classify_output['form_id']} form. Each row = {desc}. Fill only: {vars_}, and identifiers ({ids})."

import json
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path


class PlainResponse:
    """
    Base response class that wraps the raw OpenAI API response.
    Provides basic access to usage and content.
    """

    def __init__(self, raw_response):
        """
        Initialize with the raw response from self.client.chat.completions.create(**params)
        """
        self.raw_response = raw_response

    def usage(self) -> Dict[str, int]:
        """Return the usage information from the OpenAI API response."""
        if self.raw_response.usage:
            return {
                "prompt_tokens": self.raw_response.usage.prompt_tokens,
                "completion_tokens": self.raw_response.usage.completion_tokens,
                "total_tokens": self.raw_response.usage.total_tokens
            }
        return {}

    def content(self) -> str:
        """Return the content from the OpenAI API response."""
        return self.raw_response.choices[0].message.content


class IdentifyResponse(PlainResponse):
    """
    Response class for the identify step.
    Expects JSON output with format: {"printed_words": [...]}
    """

    def __init__(self, raw_response):
        super().__init__(raw_response)
        self._parsed_content = None
        self._parse_content()

    def _parse_content(self):
        """Parse the JSON content and extract printed_words."""
        content = self.content()
        try:
            parsed = json.loads(content)
            self._parsed_content = parsed
        except json.JSONDecodeError:
            raise ValueError(f"Model did not return valid JSON:\n{content}")

    def printed_words(self) -> List[str]:
        """Return the list of printed words."""
        return self._parsed_content.get("printed_words", [])

    def hash(self) -> str:
        """Return a hash of the printed_words list."""
        words = self.printed_words()
        # Create a deterministic hash of the sorted words
        words_str = "|".join(sorted(words))
        return hashlib.md5(words_str.encode()).hexdigest()

    def __str__(self):
        return f"IdentifyResponse(printed_words={self.printed_words()})"


class ClassifyResponse(PlainResponse):
    """
    Response class for the classify step.
    Expects JSON output with format: {"is_transect_subplot": bool, "forms": [...]}
    """

    def __init__(self, raw_response):
        super().__init__(raw_response)
        self._parsed_content = None
        self._parse_content()

    def _parse_content(self):
        """Parse the JSON content."""
        content = self.content()
        try:
            parsed = json.loads(content)
            self._parsed_content = parsed
        except json.JSONDecodeError:
            raise ValueError(f"Model did not return valid JSON:\n{content}")

    def is_transect_subplot(self) -> bool:
        """Return whether the study uses a transect-subplot design."""
        return self._parsed_content.get("is_transect_subplot", False)

    def forms(self) -> List[Dict[str, Any]]:
        """Return the list of form descriptions."""
        return self._parsed_content.get("forms", [])

    def get_form_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Get form template for a specific URL using source_file field."""
        filename = Path(url).name.lower().strip()
        for form in self.forms():
            # See prompt for why this is necessary. Sometimes the model
            # otherwise forgets to include source_file, or includes it as a
            # random index. So we indicate that this is the source_file: field
            # we want you to include.
            if form.get("source_file").replace("source_file: ", "").lower().strip() == filename:
                return form
        return None

    # DEPRECATED
    def form_instructions(self) -> List[str]:
        """Return form instructions for each form."""
        instructions = []
        for form in self.forms():
            form_id = form.get("form_id", "")
            row_represents = form.get("row_represents", "")
            row_variables = ", ".join(form.get("row_variables", []))
            id_variables = ", ".join(form.get("id_variables", []))

            instruction = f"This is {form_id} form. Each row = {row_represents}. Fill only: {row_variables}, and identifiers ({id_variables})."
            instructions.append(instruction)

        return instructions

    def get_form_instruction_by_url(self, url: str) -> Optional[str]:
        """Get form instruction for a specific URL using source_file field."""
        form = self.get_form_by_url(url)
        if not form:
            return None

        form_id = form.get("form_id", "")
        row_represents = form.get("row_represents", "")
        row_variables = ", ".join(form.get("row_variables", []))
        id_variables = ", ".join(form.get("id_variables", []))
        empty_fields_policy = form.get("empty_fields_policy", "")

        return f"This is {form_id} form. Each row = {row_represents}. Fill only: {row_variables}, and identifiers ({id_variables}). Policy for empty fields: {empty_fields_policy}"

    def __str__(self):
        return f"ClassifyResponse(is_transect_subplot={self.is_transect_subplot()}, forms={self.forms()}, form_instructions={self.form_instructions()})"


class ExtractResponse(PlainResponse):
    """
    Response class for the extract step.
    Expects JSON array output with extracted data objects.
    """

    def __init__(self, raw_response):
        super().__init__(raw_response)
        self._parsed_content = None
        self._parse_content()

    def _parse_content(self):
        """Parse the JSON content."""
        content = self.content()
        try:
            parsed = json.loads(content)
            # Ensure it's a list
            self._parsed_content = parsed if isinstance(
                parsed, list) else [parsed]
        except json.JSONDecodeError:
            raise ValueError(f"Model did not return valid JSON:\n{content}")

    def extracted_data(self) -> List[Dict[str, Any]]:
        """Return the list of extracted data objects."""
        return self._parsed_content

    def count_records(self) -> int:
        """Return the number of extracted records."""
        return len(self._parsed_content)

    def __str__(self):
        return f"ExtractResponse(extracted_data={self.extracted_data()})"

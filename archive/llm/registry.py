import json
from pathlib import Path
from typing import Dict, List, Optional, Any


class FormRegistry:
    """
    Manages persistent form registry with URL->hash and hash->template mappings.
    Stores both raw form template data and processed form instruction strings.
    """

    def __init__(self, registry_path: str):
        self.registry_path = Path(registry_path)
        self.data = self._load_registry()

    def _load_registry(self) -> Dict[str, Any]:
        """Load existing registry or create new one."""
        if self.registry_path.exists():
            try:
                return json.loads(self.registry_path.read_text())
            except (json.JSONDecodeError, FileNotFoundError):
                pass

        # Return empty registry structure
        return {
            "url_to_hash": {},
            "hash_to_form_template": {},
            "hash_to_form_instruction": {}
        }

    def save(self):
        """Write registry back to file."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.registry_path.write_text(json.dumps(self.data, indent=2))

    # URL-to-Hash Management
    def get_hash_for_url(self, url: str) -> Optional[str]:
        """Get hash for a URL if it exists."""
        return self.data["url_to_hash"].get(url)

    def set_hash_for_url(self, url: str, hash: str):
        """Store URL->hash mapping."""
        self.data["url_to_hash"][url] = hash

    # Hash-to-Template Management
    def has_form_template(self, hash: str) -> bool:
        """Check if hash has a saved form template."""
        return hash in self.data["hash_to_form_template"]

    def get_form_template(self, hash: str) -> Optional[Dict[str, Any]]:
        """Get form template for hash."""
        return self.data["hash_to_form_template"].get(hash)

    def set_form_template(self, hash: str, form_template: Dict[str, Any]):
        """Store form template for hash."""
        self.data["hash_to_form_template"][hash] = form_template

    # Hash-to-Instruction Management
    def has_form_instruction(self, hash: str) -> bool:
        """Check if hash has a saved form instruction."""
        return hash in self.data["hash_to_form_instruction"]

    def get_form_instruction(self, hash: str) -> Optional[str]:
        """Get form instruction for hash."""
        return self.data["hash_to_form_instruction"].get(hash)

    def set_form_instruction(self, hash: str, form_instruction: str):
        """Store form instruction for hash."""
        self.data["hash_to_form_instruction"][hash] = form_instruction

    # Batch Operations
    def get_urls_needing_identification(self, urls: List[str]) -> List[str]:
        """Return URLs that don't have hashes yet."""
        return [url for url in urls if url not in self.data["url_to_hash"]]

    def get_urls_needing_classification(self, urls: List[str]) -> List[str]:
        """Return URLs that have hashes but no form templates."""
        urls_needing_classification = []
        for url in urls:
            hash = self.get_hash_for_url(url)
            if hash and not self.has_form_template(hash):
                urls_needing_classification.append(url)
        return urls_needing_classification

    def get_form_instructions_for_urls(self, urls: List[str]) -> Dict[str, str]:
        """Get form instructions for each URL."""
        instructions_by_url = {}
        for url in urls:
            hash = self.get_hash_for_url(url)
            if hash:
                instruction = self.get_form_instruction(hash)
                if instruction:
                    instructions_by_url[url] = instruction
        return instructions_by_url

    def get_form_templates_for_urls(self, urls: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get form templates for each URL."""
        templates_by_url = {}
        for url in urls:
            hash = self.get_hash_for_url(url)
            if hash:
                template = self.get_form_template(hash)
                if template:
                    templates_by_url[url] = template
        return templates_by_url

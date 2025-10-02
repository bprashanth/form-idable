"""
A CLI tool that takes in a list of image URLs and runs the OCR pipeline on them.

# Single image
python main.py --images https://example.com/form.jpg --identify

# Multiple images
python main.py --images https://example.com/form1.jpg https://example.com/form2.jpg https://example.com/form3.jpg --identify --classify

# With custom env file
python main.py --env_path /path/to/my/.env --images https://example.com/form.jpg --extract

# Multiple images multiple steps 
python main.py --images https://example.com/image1.jpg --images https://example.com/image2.jpg --identify --classify --extract

# With debug mode to see costs
python main.py --images https://example.com/form.jpg --identify --debug
"""

#!/usr/bin/env python3
import argparse
import json
import hashlib
import os
from pathlib import Path

from client import ModelClient
from registry import FormRegistry
from response import IdentifyResponse, ClassifyResponse, ExtractResponse
from prompt import IdentifyPrompt, ClassifyPrompt, ExtractPrompt
from cost import CostCalculator


def load_species_names(species_dict_path):
    """Load species_dict.json and return sorted list of abbr+toda names."""
    with open(species_dict_path, "r", encoding="utf-8") as f:
        species_dict = json.load(f)
    names = set()
    for entry in species_dict:
        if entry.get("abbr"):
            names.add(entry.get("abbr").strip())
        if entry.get("toda_name"):
            names.add(entry.get("toda_name").strip())
    return sorted(names)


def load_env_file(env_path):
    """Load environment variables from .env file."""
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env_path", default="./.env",
                        help="Path to .env file")
    parser.add_argument(
        "--schema_path", default="./schema.json", help="Path to schema.json")
    parser.add_argument("--species_dict_path",
                        default="./species_dict.json", help="Path to species_dict.json")
    parser.add_argument("--extract_prompt",
                        default="./prompts/extract_prompt.txt", help="Path to extract_prompt.txt")
    parser.add_argument("--db_path", default="./db.json",
                        help="Path to db.json")
    parser.add_argument("--form_registry_path",
                        default="./form_registry.json", help="Path to form_registry.json")
    parser.add_argument("--identify_prompt", default="./prompts/identify_prompt.txt",
                        help="Path to identify_prompt.txt")
    parser.add_argument("--classify_prompt", default="./prompts/classify_prompt.txt",
                        help="Path to classify_prompt.txt")
    parser.add_argument("--images", nargs="+",
                        required=True, help="List of image URLs")
    parser.add_argument("--model", default="gpt-5-mini", help="Model name")
    parser.add_argument("--identify", action="store_true", default=False,
                        help="Run identify step")
    parser.add_argument("--classify", action="store_true", default=False,
                        help="Run classify step")
    parser.add_argument("--extract", action="store_true", default=False,
                        help="Run extract step")
    parser.add_argument("--debug", action="store_true", default=False,
                        help="Enable debug mode to show API costs")
    args = parser.parse_args()

    # Load environment variables
    env_vars = load_env_file(args.env_path)
    api_key = env_vars.get("OPEN_AI_API_KEY")
    if not api_key:
        raise ValueError(f"OPEN_AI_API_KEY not found in {args.env_path}")

    # Load species names
    species_names = load_species_names(args.species_dict_path)

    # Init client and cost calculator
    client = ModelClient(api_key=api_key, model=args.model)
    cost_calculator = CostCalculator()

    # Init form registry
    registry = FormRegistry(args.form_registry_path)

    # import pudb
    # pudb.set_trace()

    # Step 0: Identify
    if args.identify:
        identify_prompt = IdentifyPrompt(args.identify_prompt)

        # Get URLs that need identification
        urls_needing_id = registry.get_urls_needing_identification(args.images)
        print(f"URLs needing identification: {urls_needing_id}")

        identify_responses = {}
        for image_url in urls_needing_id:
            raw_identify_response = client.infer(identify_prompt, image_url)
            identify_response = IdentifyResponse(raw_identify_response)
            identify_responses[image_url] = identify_response
            if args.debug:
                print(f"IDENTIFY[{image_url}]: {identify_response}")

            # Store URL->hash mapping
            hash = identify_response.hash()
            registry.set_hash_for_url(image_url, hash)

        if args.debug:
            for image_url, resp in identify_responses.items():
                cost_calculator.print_cost(
                    f"IDENTIFY[{image_url}]", resp.usage(), args.model)

        # Save registry after identification
        registry.save()
    else:
        print("Skipping identify step")

    # Step 1: Classify
    # Typically this step runs for _all_ forms in the study in the first shot,
    # because we're trying to understand the nature of the study in the first
    # place - i.e. is it even a transect study?
    if args.classify:
        classify_prompt = ClassifyPrompt(args.classify_prompt)

        # Get URLs that need classification
        urls_needing_classification = registry.get_urls_needing_classification(
            args.images)

        if urls_needing_classification:
            print(
                f"URLs needing classification: {urls_needing_classification}")

            # Run classification in batch mode for _all_ URLs if any of them
            # need classification.
            raw_classify_response = client.infer(
                classify_prompt, args.images)
            classify_response = ClassifyResponse(raw_classify_response)

            # Map results back to individual URLs using source_file field
            for image_url in urls_needing_classification:
                # Get hash for this URL
                hash = registry.get_hash_for_url(image_url)

                # Get form template and instruction for this specific URL
                form = classify_response.get_form_by_url(image_url)
                form_instruction = classify_response.get_form_instruction_by_url(
                    image_url)
                if args.debug:
                    print(f"CLASSIFY[{image_url}]: {form}")
                    print(f"CLASSIFY[{image_url}]: {form_instruction}")

                if form and form_instruction:
                    registry.set_form_template(hash, form)
                    registry.set_form_instruction(hash, form_instruction)
                    print(
                        f"Stored classification for {image_url} (hash: {hash})")
                else:
                    print(
                        f"Warning: No form or form instruction found for {image_url}, skipping classification")
        else:
            print("No URLs need classification")

        if args.debug:
            # Note: In batch mode, we only have one response to show cost for
            if urls_needing_classification:
                cost_calculator.print_cost(
                    f"CLASSIFY[batch]", classify_response.usage(), args.model)

        # Save registry after classification
        registry.save()
        print(f"Saved form registry to {args.form_registry_path}")
    else:
        print("Skipping classify step")

    # Step 2: Extract
    if args.extract:
        # Get form instructions for each URL
        form_instructions_by_url = registry.get_form_instructions_for_urls(
            args.images)
        print(
            f"Form instructions by URL: {list(form_instructions_by_url.keys())}")

        extract_results = []
        form_results = []
        for image_url in args.images:
            form_instruction = form_instructions_by_url.get(image_url)
            if not form_instruction:
                print(
                    f"Warning: No form instruction found for {image_url}, skipping extraction")
                continue

            # Create extract prompt with URL-specific form instruction
            extract_prompt = ExtractPrompt(
                args.extract_prompt,
                species_names=species_names,
                form_instructions=form_instruction
            )

            # Run extraction for this single URL
            raw_extract_response = client.infer(extract_prompt, image_url)
            extract_response = ExtractResponse(raw_extract_response)
            form_results.extend(extract_response.extracted_data())
            extract_results.append(extract_response)

        # Print cost if debug mode is enabled
        if args.debug:
            print(f"EXTRACT: {form_results}")
            try:
                for i, resp in enumerate(extract_results):
                    cost_calculator.print_cost(
                        f"EXTRACT[{i}]", resp.usage(), args.model)
            except Exception as e:
                print(f"Error printing extract results: {e}")

        # Append to db.json
        db_path = Path(args.db_path)
        db = []
        if db_path.exists():
            db = json.loads(db_path.read_text())
        db.extend(form_results)
        db_path.write_text(json.dumps(db, indent=2))
        print(f"Saved extracted data to {db_path}")
    else:
        print("Skipping extract step")


if __name__ == "__main__":
    main()

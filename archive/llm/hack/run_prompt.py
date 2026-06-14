#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
from pathlib import Path

# 🔹 Global list of image URLs
IMAGE_URLS = [
    "https://fomomonguest.s3.ap-south-1.amazonaws.com/keystone/IMG-20250924-WA0000.jpg",
    # "https://fomomonguest.s3.ap-south-1.amazonaws.com/keystone/IMG-20250924-WA0001.jpg",
    # "https://fomomonguest.s3.ap-south-1.amazonaws.com/keystone/IMG-20250924-WA0002.jpg",
]


def compute_cost(response, model):
    """
    Compute the cost of an OpenAI API call given the API response JSON
    and the model name.

    Args:
        response (dict): Full API response as dict (parsed JSON).
        model (str): The model string, e.g. "gpt-4.1", "gpt-4.1-mini", "gpt-5-mini".

    Returns:
        float: Cost in USD.
    """

    # Pricing (per 1M tokens) from OpenAI docs (as of 2025-01)
    pricing = {
        "gpt-4.1": {"input": 0.002, "output": 0.008},      # $2.00 / $8.00
        "gpt-4.1-mini": {"input": 0.0004, "output": 0.0016},  # $0.40 / $1.60
        "gpt-5-mini": {"input": 0.00025, "output": 0.002},   # $0.25 / $2.00
        "gpt-5": {"input": 0.00125, "output": 0.01},         # $1.25 / $10.00
    }

    if model not in pricing:
        raise ValueError(f"Unknown model {model}, add pricing to lookup.")

    usage = response.get("usage", {})
    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)

    cost_input = prompt_tokens * pricing[model]["input"]
    cost_output = completion_tokens * pricing[model]["output"]

    # Prices are per 1M tokens, so scale down
    total_cost = (cost_input + cost_output) / 1_000_000
    return round(total_cost, 6)


def load_env(env_file):
    """Load env vars from a .env file."""
    env_vars = {}
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, value = line.split("=", 1)
            env_vars[key.strip()] = value.strip().strip('"').strip("'")
    return env_vars


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True,
                        default="gpt-5-mini",
                        help="Model name (e.g. gpt-4.1, gpt-5-mini, gpt-4.1-mini)")
    parser.add_argument("--prompt_file", required=True,
                        help="Path to prompt txt file")
    parser.add_argument("--env_file", required=True,
                        help="Path to .env with OPEN_AI_API_KEY")
    parser.add_argument("--params_file", default="params.json",
                        help="Where to write params.json")
    parser.add_argument("--output_file", default="output.json",
                        help="Where to write output.json")
    args = parser.parse_args()

    # Load env
    env_vars = load_env(args.env_file)
    api_key = env_vars.get("OPEN_AI_API_KEY")
    if not api_key:
        raise RuntimeError("OPEN_AI_API_KEY not found in env file")

    # Load prompt
    prompt_text = Path(args.prompt_file).read_text(encoding="utf-8")

    # Build messages
    messages = [
        {"role": "system", "content": "You are an OCR form classification assistant."},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt_text},
            ]
            + [{"type": "image_url", "image_url": {"url": url}}
                for url in IMAGE_URLS],
        },
    ]

    params = {
        "model": args.model,
        "messages": messages,
    }

    # Write params.json
    Path(args.params_file).write_text(
        json.dumps(params, indent=2), encoding="utf-8")
    print(f"Wrote {args.params_file}")

    # Run curl with subprocess
    curl_cmd = [
        "curl",
        "https://api.openai.com/v1/chat/completions",
        "-H", f"Authorization: Bearer {api_key}",
        "-H", "Content-Type: application/json",
        "-d", f"@{args.params_file}",
    ]
    print(f"👉 Running: {' '.join(curl_cmd)}\n")
    result = subprocess.run(curl_cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("stderr:", result.stderr)

    resp = json.loads(result.stdout)
    cost = compute_cost(resp, args.model)
    print(f"Cost: ${cost}")

    try:
        # with open(args.output_file, "w") as f:
        #     json.dump(resp["choices"][0]["message"]["content"], f, indent=2)
        import pprint
        pprint.pprint(resp["choices"][0]["message"]["content"])
    except Exception as e:
        print(f"Error writing {args.output_file}: {e}")


if __name__ == "__main__":
    main()

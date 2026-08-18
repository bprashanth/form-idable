import json
import tempfile
import unittest
from pathlib import Path

import openai_responses
import run_agentic_primary


class UsageTest(unittest.TestCase):
    def test_usage_parts_and_price_do_not_double_count_reasoning(self):
        usage = {
            "input_tokens": 1000,
            "input_tokens_details": {"cached_tokens": 200, "cache_write_tokens": 100},
            "output_tokens": 500,
            "output_tokens_details": {"reasoning_tokens": 300},
            "total_tokens": 1500,
        }
        parts = openai_responses.usage_parts(usage)
        self.assertEqual(parts["uncached_input_tokens"], 700)
        self.assertEqual(parts["reasoning_tokens"], 300)
        cost, _ = openai_responses.price_usage("gpt-5-nano", usage)
        expected = (700 * .05 + 200 * .005 + 100 * .05 * 1.25 + 500 * .4) / 1_000_000
        self.assertAlmostEqual(cost, expected)

    def test_payload_is_strict_and_embeds_image(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "x.png"
            image.write_bytes(b"png")
            schema = {"type": "object", "properties": {}, "additionalProperties": False}
            payload = openai_responses.build_payload(
                "gpt-5-nano", "read", [image], schema, reasoning="none")
        self.assertFalse(payload["store"])
        self.assertTrue(payload["text"]["format"]["strict"])
        self.assertEqual(payload["reasoning"]["effort"], "none")
        self.assertTrue(payload["input"][0]["content"][1]["image_url"].startswith("data:image/png;base64,"))
        json.dumps(payload)

    def test_payload_can_omit_reasoning_for_legacy_model(self):
        payload = openai_responses.build_payload(
            "gpt-4.1-nano", "read", [], {"type": "object"}, reasoning=None)
        self.assertNotIn("reasoning", payload)
        self.assertNotIn("verbosity", payload["text"])

    def test_nested_codex_usage_and_pricing(self):
        event = {"type": "token_count", "payload": {"token_usage": {
            "input_tokens": 1000, "cached_input_tokens": 200,
            "cache_write_input_tokens": 100, "output_tokens": 500,
            "reasoning_output_tokens": 300, "total_tokens": 1500,
        }}}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            path.write_text(json.dumps(event) + "\n")
            events = run_agentic_primary.usage_events(path)
        self.assertEqual(events[0]["usage"]["reasoning_output_tokens"], 300)
        self.assertEqual(run_agentic_primary.final_usage(events)["input_tokens"], 1000)
        priced = run_agentic_primary.price_codex_usage("gpt-5.6-sol", events[0]["usage"])
        expected = (700 * 5 + 200 * .5 + 100 * 5 * 1.25 + 500 * 30) / 1_000_000
        self.assertAlmostEqual(priced["cost_usd"], expected)
        self.assertEqual(priced["cost_usd_range"], [priced["cost_usd"], priced["cost_usd"]])
        self.assertTrue(priced["cache_write_bucket_reported"])

    def test_missing_cache_write_bucket_produces_cost_range(self):
        usage = {"input_tokens": 1000, "cached_input_tokens": 200,
                 "output_tokens": 500}
        priced = run_agentic_primary.price_codex_usage("gpt-5.6-sol", usage)
        lower = (800 * 5 + 200 * .5 + 500 * 30) / 1_000_000
        upper = (800 * 5 * 1.25 + 200 * .5 + 500 * 30) / 1_000_000
        self.assertEqual(priced["cost_usd_range"], [lower, upper])
        self.assertFalse(priced["cache_write_bucket_reported"])

    def test_credit_exhaustion_is_detected_from_jsonl(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            path.write_text('{"type":"error","message":"You have no credits remaining"}\n')
            self.assertTrue(run_agentic_primary.credit_exhausted(path))


if __name__ == "__main__":
    unittest.main()

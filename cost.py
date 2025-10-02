
class CostCalculator:
    """Calculate OpenAI API costs based on model and usage."""

    def __init__(self):
        # Pricing (per 1M tokens) from OpenAI docs (as of 2025-01)
        self.pricing = {
            "gpt-4.1": {"input": 2.00, "output": 8.00},      # $2.00 / $8.00
            "gpt-4.1-mini": {"input": 0.40, "output": 1.60},  # $0.40 / $1.60
            "gpt-5-mini": {"input": 0.25, "output": 2.00},   # $0.25 / $2.00
            "gpt-5": {"input": 1.25, "output": 10.00},      # $1.25 / $10.00
            # $1.25 / $10.00
            "gpt-5-chat-latest": {"input": 1.25, "output": 10.00},
            "gpt-5-codex": {"input": 1.25, "output": 10.00},  # $1.25 / $10.00
        }

    def compute_cost(self, usage, model):
        """
        Compute the cost of an OpenAI API call given the API response JSON
        and the model name.

        @param usage (dict): Full API response as dict (parsed JSON).
        @param model (str): The model string, e.g. "gpt-4.1", "gpt-4.1-mini", "gpt-5-mini".

        @return: Cost in USD.
        """
        if model not in self.pricing:
            raise ValueError(f"Unknown model {model}, add pricing to lookup.")

        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)

        cost_input = prompt_tokens * self.pricing[model]["input"]
        cost_output = completion_tokens * self.pricing[model]["output"]

        # Prices are per 1M tokens, so scale down
        total_cost = (cost_input + cost_output) / 1_000_000
        return round(total_cost, 6)

    def print_cost(self, step_name, usage, model):
        """Print cost information for a step if debug mode is enabled."""
        try:
            cost = self.compute_cost(usage, model)
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)

            # Format cost display - show cents if cost is less than $1
            if cost < 1.0:
                cost_display = f"${cost:.4f} ({cost*100:.2f}¢)"
            else:
                cost_display = f"${cost:.4f}"

            print(f"[DEBUG] {step_name} cost: {cost_display} "
                  f"(prompt: {prompt_tokens:,} tokens, "
                  f"completion: {completion_tokens:,} tokens)")
        except Exception as e:
            print(f"[DEBUG] Could not calculate cost for {step_name}: {e}")

"""Experiment 3: Claude (ANTHROPIC_API_KEY_NEW), crop-friendly prompt, high max_turns.

Runs system_prompt_crops.md against /tmp/experiments/exp3/ which already
has input.pdf, render_page.py, v1.json, v1_overview.png. Comparable to
Experiment 2 (Codex CLI) — same prompt family, crops allowed, generous
turn budget.
"""

import asyncio
import os
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
    query,
)

PROMPT_PATH = Path("/tmp/experiments/shared/system_prompt_crops.md")
WORKDIR = Path("/tmp/experiments/exp3")
RENDER_TOOL_PATH = WORKDIR / "render_page.py"

LOG_TRUNCATE_LIMIT = 300


def _truncate(value, limit: int = LOG_TRUNCATE_LIMIT) -> str:
    s = str(value)
    if len(s) <= limit:
        return s
    return f"{s[:limit]}... ({len(s)} chars total)"


def _truncate_input(input_value):
    if not isinstance(input_value, dict):
        return _truncate(input_value)
    return {k: _truncate(v) for k, v in input_value.items()}


def _summarize_content(content):
    if content is None or isinstance(content, str):
        return _truncate(content)
    if isinstance(content, list):
        summary = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "image":
                source = item.get("source", {})
                data = source.get("data", "")
                media_type = source.get("media_type", "unknown")
                summary.append(f"<image {media_type}, {len(data)} chars base64>")
            elif isinstance(item, dict) and "text" in item:
                summary.append(_truncate(item["text"]))
            else:
                summary.append(_truncate(item))
        return summary
    return _truncate(content)


def _log_block(prefix: str, block) -> None:
    if isinstance(block, TextBlock):
        print(f"[{prefix}] {_truncate(block.text)}")
    elif isinstance(block, ToolUseBlock):
        print(f"[{prefix}:tool_use] {block.name} {_truncate_input(block.input)}")
    elif isinstance(block, ToolResultBlock):
        print(f"[{prefix}:tool_result] error={block.is_error} {_summarize_content(block.content)}")
    else:
        print(f"[{prefix}] {_truncate(block)}")


def _log_message(message) -> None:
    if isinstance(message, (AssistantMessage, UserMessage)):
        content = message.content
        blocks = content if isinstance(content, list) else [content]
        prefix = type(message).__name__.replace("Message", "").lower()
        for block in blocks:
            _log_block(prefix, block)
    elif isinstance(message, ResultMessage):
        print(
            f"[result] subtype={message.subtype} turns={message.num_turns} "
            f"cost_usd={message.total_cost_usd} error={message.is_error}"
        )
    else:
        print(f"[{type(message).__name__}] {_truncate(message)}")


async def main():
    page = 1
    input_name = "input.pdf"

    system_prompt = (
        PROMPT_PATH.read_text()
        .replace("{input_file}", input_name)
        .replace("{page}", str(page))
        .replace("{render_tool}", str(RENDER_TOOL_PATH))
    )

    venv_bin = "/home/desinotorious/src/github.com/bprashanth/good-shepherd/agents/formidable/.venv/bin"
    env = dict(os.environ)
    env["PATH"] = f"{venv_bin}:{env.get('PATH', '')}"
    # ANTHROPIC_API_KEY_NEW is a `claude setup-token` long-lived OAuth token
    # (sk-ant-oat...), not a console API key — the CLI reads OAuth tokens
    # via CLAUDE_CODE_OAUTH_TOKEN, and ANTHROPIC_API_KEY must be unset or
    # the CLI prefers it.
    env.pop("ANTHROPIC_API_KEY", None)
    env["CLAUDE_CODE_OAUTH_TOKEN"] = os.environ["ANTHROPIC_API_KEY_NEW"]

    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        tools=["Bash", "Read", "Write", "Glob"],
        permission_mode="bypassPermissions",
        cwd=str(WORKDIR),
        model="sonnet",
        max_turns=30,
        env=env,
    )

    v1_note = (
        "v1.json (Textract's structured read of this page) and "
        "v1_overview.png (a rendered overview) are already present in "
        "your current directory (run `ls` to confirm)."
    )
    prompt = (
        f"Transcribe page {page} of {input_name} into output.xlsx as "
        f"described in your instructions. {v1_note} Begin now."
    )

    async for message in query(prompt=prompt, options=options):
        _log_message(message)


if __name__ == "__main__":
    asyncio.run(main())

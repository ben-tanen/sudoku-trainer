"""Model-agnostic LLM adapter. Auto-detects provider from available API keys."""

from __future__ import annotations

import logging
import os

log = logging.getLogger(__name__)


def _detect_provider() -> tuple[str, str] | None:
    """Auto-detect provider from env vars. Returns (provider, api_key) or None."""
    for env_var, provider in [
        ("ANTHROPIC_API_KEY", "anthropic"),
        ("OPENAI_API_KEY", "openai"),
        ("GEMINI_API_KEY", "gemini"),
    ]:
        key = os.environ.get(env_var)
        if key:
            return provider, key
    return None


# Default models per provider — cheap/fast options suitable for a tutor
DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-20250514",
    "openai": "gpt-4o-mini",
    "gemini": "gemini-2.5-flash",
}


def get_provider_info() -> dict:
    """Return current provider status for the frontend."""
    detected = _detect_provider()
    if detected:
        provider, _ = detected
        return {
            "provider": provider,
            "model": os.environ.get("SUDOKU_LLM_MODEL", DEFAULT_MODELS[provider]),
            "available": True,
        }
    return {"provider": None, "model": None, "available": False}


async def complete(
    system: str,
    messages: list[dict[str, str]],
    max_tokens: int = 2000,
) -> str:
    """Send a chat completion request to whichever provider is configured.

    Args:
        system: system prompt
        messages: list of {"role": "user"|"assistant", "content": "..."}
        max_tokens: max response tokens

    Returns:
        The assistant's response text.

    Raises:
        RuntimeError if no provider is configured.
    """
    detected = _detect_provider()
    if not detected:
        raise RuntimeError("No LLM API key configured")

    provider, api_key = detected
    model = os.environ.get("SUDOKU_LLM_MODEL", DEFAULT_MODELS[provider])

    msg_count = len(messages)
    last_msg_len = len(messages[-1]["content"]) if messages else 0
    log.info(f"[complete] provider={provider} model={model} max_tokens={max_tokens} messages={msg_count} last_msg_chars={last_msg_len}")

    if provider == "anthropic":
        result = _call_anthropic(api_key, model, system, messages, max_tokens)
    elif provider == "openai":
        result = _call_openai(api_key, model, system, messages, max_tokens)
    elif provider == "gemini":
        result = _call_gemini(api_key, model, system, messages, max_tokens)
    else:
        raise RuntimeError(f"Unknown provider: {provider}")

    log.info(f"[complete] response_chars={len(result) if result else 0} response_preview={repr(result[:100]) if result else 'None'}...")
    return result


def _call_anthropic(
    api_key: str, model: str, system: str,
    messages: list[dict], max_tokens: int,
) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=messages,
    )
    return response.content[0].text


def _call_openai(
    api_key: str, model: str, system: str,
    messages: list[dict], max_tokens: int,
) -> str:
    import openai
    client = openai.OpenAI(api_key=api_key)
    oai_messages = [{"role": "system", "content": system}] + messages
    response = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=oai_messages,
    )
    return response.choices[0].message.content


def _call_gemini(
    api_key: str, model: str, system: str,
    messages: list[dict], max_tokens: int,
) -> str:
    from google import genai
    client = genai.Client(api_key=api_key)

    # Convert messages to Gemini's Content format
    contents = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(genai.types.Content(
            role=role,
            parts=[genai.types.Part(text=msg["content"])],
        ))

    # Thinking models (2.5+) share max_output_tokens between thinking and response.
    # Set an explicit thinking budget so it doesn't consume the output budget.
    thinking_config = None
    if "2.5" in model or "2.0" in model:
        thinking_config = genai.types.ThinkingConfig(thinking_budget=1024)
        log.info(f"[gemini] thinking model detected, thinking_budget=1024")

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=genai.types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_tokens,
            thinking_config=thinking_config,
        ),
    )

    # Log Gemini-specific metadata
    candidate = response.candidates[0] if response.candidates else None
    finish_reason = candidate.finish_reason if candidate else "no_candidate"
    usage = response.usage_metadata
    log.info(
        f"[gemini] finish_reason={finish_reason} "
        f"prompt_tokens={usage.prompt_token_count if usage else '?'} "
        f"response_tokens={usage.candidates_token_count if usage else '?'} "
        f"total_tokens={usage.total_token_count if usage else '?'}"
    )
    return response.text


_OCR_PROMPT = """\
Extract the 9x9 sudoku grid from this image.

Step 1: Read the grid row by row. For each row, list the 9 cells left to right. Use the thick 3x3 box borders to stay aligned. Write each row on its own line as: Row N: d,d,d,d,d,d,d,d,d (use 0 for empty cells).

Step 2: After listing all 9 rows, convert to a JSON array.

IMPORTANT:
- The grid has 9 rows and 9 columns. Each 3x3 box is separated by thick borders.
- Ignore anything outside the grid (buttons, timers, UI elements).
- A cell with ANY visible digit (1-9) should be recorded, regardless of text color or background color.
- A cell with no digit is 0.
- Count carefully: each row must have exactly 9 values, one per column.

Now read the grid:"""

_OCR_EXTRACT = """\
Now convert your row-by-row reading into a single JSON array of 9 arrays. Output ONLY the JSON, no other text.
Example format: [[0,0,3,0,2,0,6,0,0],[9,0,0,3,0,5,0,0,1],...]"""


async def extract_grid_from_image(image_bytes: bytes, mime_type: str) -> list[list[int]]:
    """Send an image to Gemini Flash vision and extract a 9x9 sudoku grid."""
    import json, re

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("OCR requires a GEMINI_API_KEY to be configured")

    from google import genai
    client = genai.Client(api_key=api_key)
    model = os.environ.get("SUDOKU_OCR_MODEL", "gemini-2.5-pro")
    log.info(f"[ocr] model={model} mime_type={mime_type} image_bytes={len(image_bytes)}")

    # Pass 1: read the grid row-by-row (chain of thought)
    contents = [
        genai.types.Content(
            role="user",
            parts=[
                genai.types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                genai.types.Part(text=_OCR_PROMPT),
            ],
        )
    ]

    config = genai.types.GenerateContentConfig(
        max_output_tokens=8000,
        temperature=0,
        thinking_config=genai.types.ThinkingConfig(thinking_budget=1024),
    )

    pass1 = client.models.generate_content(
        model=model, contents=contents, config=config,
    )

    if not pass1.text:
        # Log the full response for debugging
        log.error(f"[ocr] pass 1 returned no text. candidates: {pass1.candidates}")
        raise RuntimeError("Gemini returned an empty response — the model may be overloaded. Try again.")

    reading = pass1.text.strip()
    log.info(f"[ocr] pass 1 (row-by-row reading):\n{reading}")

    # Pass 2: convert the reading to clean JSON
    contents.append(genai.types.Content(
        role="model", parts=[genai.types.Part(text=reading)],
    ))
    contents.append(genai.types.Content(
        role="user", parts=[genai.types.Part(text=_OCR_EXTRACT)],
    ))

    pass2 = client.models.generate_content(
        model=model, contents=contents, config=config,
    )

    if not pass2.text:
        log.error(f"[ocr] pass 2 returned no text. candidates: {pass2.candidates}")
        raise RuntimeError("Gemini returned an empty response on pass 2. Try again.")

    text = pass2.text.strip()
    log.info(f"[ocr] pass 2 (JSON):\n{text}")

    # Strip markdown code fences if present
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    # Extract the first JSON array if there's surrounding text
    match = re.search(r"\[[\s\S]*\]", text)
    if match:
        text = match.group(0)

    grid = json.loads(text)

    # Validate shape and values
    if not isinstance(grid, list) or len(grid) != 9:
        raise ValueError("Response is not a 9-row grid")
    for row in grid:
        if not isinstance(row, list) or len(row) != 9:
            raise ValueError("Each row must have 9 cells")
        for val in row:
            if not isinstance(val, int) or val < 0 or val > 9:
                raise ValueError(f"Invalid cell value: {val}")

    return grid

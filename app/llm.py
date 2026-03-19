"""Model-agnostic LLM adapter. Auto-detects provider from available API keys."""

from __future__ import annotations

import os


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
    max_tokens: int = 500,
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

    if provider == "anthropic":
        return _call_anthropic(api_key, model, system, messages, max_tokens)
    elif provider == "openai":
        return _call_openai(api_key, model, system, messages, max_tokens)
    elif provider == "gemini":
        return _call_gemini(api_key, model, system, messages, max_tokens)
    else:
        raise RuntimeError(f"Unknown provider: {provider}")


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

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=genai.types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_tokens,
        ),
    )
    return response.text

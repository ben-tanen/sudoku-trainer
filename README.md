# Sudoku Trainer

A sudoku tutor that helps you learn solving techniques — not just solve puzzles. Enter a puzzle, get stuck, and ask for hints that guide you toward the answer without giving it away.

## Features

- **Keyboard-driven grid** — arrow keys to navigate, digits to fill, Shift+Tab to cycle input modes (Given / Solved / Pencil)
- **Technique-aware solver** — identifies the simplest applicable technique from 16 strategies across 4 difficulty tiers (Beginner → Expert)
- **Conversational tutor** — LLM-powered hints that respect your skill level: nudges for techniques you know, gentle introductions for new ones
- **Skill profile** — track which techniques you've learned; the tutor adapts hint depth accordingly (persisted in localStorage)
- **Auto-candidates** — toggle computed candidates for all empty cells
- **Digit highlighting** — click a digit to highlight all instances; selected row/col/box highlighted automatically
- **Technique tooltips** — hover over technique names in chat for quick descriptions

## Techniques

| Tier | Techniques |
|------|-----------|
| Beginner | Naked Single, Hidden Single |
| Intermediate | Naked Pair/Triple, Hidden Pair/Triple, Pointing Pair, Box/Line Reduction |
| Advanced | X-Wing, Swordfish, XY-Wing, Simple Coloring |
| Expert | Jellyfish, Unique Rectangle, XYZ-Wing, Forcing Chain |

## Setup

Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/).

```bash
# Install dependencies
make install

# Run (with 1Password secret references)
make run

# Or run directly with an API key
GEMINI_API_KEY=your-key uv run uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000.

## LLM Providers

The tutor supports multiple LLM providers — it auto-detects based on which API key is set (checked in order):

| Provider | Env Var | Default Model |
|----------|---------|---------------|
| Anthropic (Claude) | `ANTHROPIC_API_KEY` | claude-sonnet-4-20250514 |
| OpenAI (GPT) | `OPENAI_API_KEY` | gpt-4o-mini |
| Google (Gemini) | `GEMINI_API_KEY` | gemini-2.5-flash |

Override the model with `SUDOKU_LLM_MODEL=model-name`.

If no API key is set, hints fall back to templates generated from the solver output. The solver and grid work fully offline.

## Stack

- **Frontend**: vanilla JS, CSS, DOM-based grid
- **Backend**: Python, FastAPI
- **Solver**: custom technique detection engine (no external solver libraries)
- **Tutor**: LLM via provider-agnostic adapter

"""Conversational tutor. Uses LLM when available, falls back to templates."""

from __future__ import annotations

from app.llm import complete, get_provider_info
from app.models import TechniqueResult

TIER_ORDER = {"beginner": 0, "intermediate": 1, "advanced": 2, "expert": 3}

TECHNIQUE_TIERS = {
    "naked_single": "beginner", "hidden_single": "beginner",
    "naked_pair": "intermediate", "naked_triple": "intermediate",
    "hidden_pair": "intermediate", "hidden_triple": "intermediate",
    "pointing_pair": "intermediate", "box_line_reduction": "intermediate",
    "x_wing": "advanced", "swordfish": "advanced",
    "xy_wing": "advanced", "simple_coloring": "advanced",
    "jellyfish": "expert", "unique_rectangle": "expert",
    "xyz_wing": "expert", "forcing_chain": "expert",
}

# Short descriptions for template-based hints
TECHNIQUE_DESCRIPTIONS = {
    "naked_single": "A cell where all but one candidate has been eliminated. Only one digit can go there.",
    "hidden_single": "A digit that can only go in one cell within a row, column, or box — even if that cell has other candidates.",
    "naked_pair": "Two cells in the same unit that share the same two candidates. Those digits can be removed from other cells in the unit.",
    "naked_triple": "Three cells in a unit whose combined candidates form a set of exactly three digits. Those digits can be removed from other cells.",
    "hidden_pair": "Two digits that only appear as candidates in the same two cells of a unit. Other candidates can be removed from those cells.",
    "hidden_triple": "Three digits that only appear in three cells of a unit. Other candidates can be removed from those cells.",
    "pointing_pair": "A digit's candidates within a box are all in the same row or column. That digit can be removed from the rest of that row/column.",
    "box_line_reduction": "A digit's candidates in a row/column all fall within one box. That digit can be removed from other cells in that box.",
    "x_wing": "A digit appears in exactly two cells in two different rows, and those cells share the same two columns (forming a rectangle). The digit can be eliminated from other cells in those columns.",
    "swordfish": "Like X-Wing but with three rows and three columns forming the pattern.",
    "xy_wing": "Three cells with two candidates each: a pivot cell shares one candidate with each wing. The digit shared by both wings can be eliminated from cells that see both wings.",
    "simple_coloring": "Following chains of conjugate pairs for a single digit to find contradictions or eliminations.",
    "jellyfish": "Like X-Wing/Swordfish but with four rows and four columns.",
    "unique_rectangle": "Avoiding a deadly pattern (rectangle of four cells with the same two candidates) that would give the puzzle multiple solutions.",
    "xyz_wing": "Like XY-Wing but the pivot has three candidates. The digit common to all three cells can be eliminated from cells seeing all three.",
    "forcing_chain": "Testing each candidate in a cell — if all possibilities lead to the same conclusion, that conclusion must be true.",
}


def get_user_max_tier(skill_profile: dict[str, bool]) -> int:
    max_tier = 0
    for technique_id, known in skill_profile.items():
        if known and technique_id in TECHNIQUE_TIERS:
            tier = TIER_ORDER.get(TECHNIQUE_TIERS[technique_id], 0)
            max_tier = max(max_tier, tier)
    return max_tier


def get_hint_level(technique: TechniqueResult, skill_profile: dict[str, bool]) -> str:
    technique_tier = TIER_ORDER.get(technique.tier, 0)
    user_max_tier = get_user_max_tier(skill_profile)
    is_known = skill_profile.get(technique.technique_id, False)

    if is_known:
        return "nudge"
    elif technique_tier <= user_max_tier + 1:
        return "introduce"
    else:
        return "skip"


def build_system_prompt(skill_profile: dict[str, bool]) -> str:
    known = [tid for tid, v in skill_profile.items() if v and tid in TECHNIQUE_TIERS]
    unknown = [tid for tid, v in skill_profile.items() if not v and tid in TECHNIQUE_TIERS]

    known_str = ", ".join(t.replace("_", " ").title() for t in known) or "none yet"
    unknown_str = ", ".join(t.replace("_", " ").title() for t in unknown) or "none"

    return f"""You are a sudoku tutor. Your job is to help the user learn sudoku-solving techniques — NOT to solve the puzzle for them.

RULES:
1. NEVER tell the user the value of a specific cell unless they explicitly ask "what is the answer for RxCx?"
2. Guide them toward finding the answer themselves.
3. When giving hints, focus on WHERE to look and WHAT technique to apply, not the specific digits.
4. If the user asks follow-up questions about a technique, explain it conceptually with examples.
5. Use cell references like R3C5 (Row 3, Column 5) when referring to cells.
6. Be encouraging but concise.

HANDLING FOLLOW-UP QUESTIONS:
- If the user asks "what is [technique]?" or "what does [technique] mean?", they are asking you to EXPLAIN the technique — do NOT treat this as them saying the hint was wrong. Just explain the concept clearly.
- If the user says they found/placed a digit and asks for confirmation, CHECK the solver's technique result (provided below) to verify. The technique result tells you exactly which cell and digit the solver identified. Confirm if they got it right, or gently redirect if they got the wrong cell/digit.
- The user may have already entered their answer into the grid before asking for confirmation — that's fine. Use the solver's technique result (not just the current grid state) to verify their answer.
- Keep your responses concise. Don't over-explain unless the user asks for more detail.

The user's skill profile:
- Techniques they know: {known_str}
- Techniques they're learning: {unknown_str}

HINT LEVELS based on technique familiarity:
- For techniques the user KNOWS: give a brief nudge — just point to the area and name the technique. Example: "There's a Naked Pair opportunity in Row 3."
- For techniques ONE TIER above the user's level: introduce the technique gently. Example: "There's a technique called X-Wing that applies here. It works by finding a digit that appears in exactly two cells in two different rows, forming a rectangle pattern. Want me to explain more?"
- For techniques TWO+ TIERS above: say "This puzzle requires techniques beyond your current level" and suggest they try a different puzzle, or offer to introduce the technique if they're curious.

When explaining a technique, use this structure:
1. What the technique is (one sentence)
2. How to spot it (what pattern to look for)
3. Where it applies in this puzzle (general area, not specific digits)
4. What it lets you do (eliminate candidates or place a digit)"""


def format_grid_for_llm(grid: list[list[int]]) -> str:
    lines = ["    C1 C2 C3  C4 C5 C6  C7 C8 C9"]
    for r in range(9):
        row_str = f"R{r+1}  "
        for c in range(9):
            val = grid[r][c]
            row_str += f" {val if val else '.'} "
            if c in (2, 5):
                row_str += "|"
        lines.append(row_str)
        if r in (2, 5):
            lines.append("    " + "-" * 30)
    return "\n".join(lines)


def build_hint_message(
    technique: TechniqueResult, hint_level: str, grid: list[list[int]],
) -> str:
    grid_text = format_grid_for_llm(grid)

    if hint_level == "nudge":
        return (
            f"Current puzzle state:\n{grid_text}\n\n"
            f"The solver found a **{technique.technique_name}** opportunity. "
            f"Context: {technique.explanation_context}\n\n"
            f"Give the user a brief NUDGE — name the technique and the general area "
            f"(row/column/box), but do NOT reveal the specific digit or cell value. "
            f"Keep it to 1-2 sentences."
        )
    elif hint_level == "introduce":
        return (
            f"Current puzzle state:\n{grid_text}\n\n"
            f"The solver found a **{technique.technique_name}** opportunity. "
            f"Context: {technique.explanation_context}\n\n"
            f"The user hasn't learned this technique yet. INTRODUCE it gently:\n"
            f"1. Explain what the technique is in simple terms\n"
            f"2. Describe the pattern to look for\n"
            f"3. Point to the general area where it applies (row/box number, not specific values)\n"
            f"Do NOT reveal the specific answer. Encourage them to try spotting it themselves."
        )
    else:
        return (
            f"Current puzzle state:\n{grid_text}\n\n"
            f"The solver found a technique ({technique.technique_name}, "
            f"tier: {technique.tier}) that is well beyond the user's current level. "
            f"Let them know this puzzle may require techniques they haven't learned yet, "
            f"and suggest they either try a different puzzle or ask if they'd like to "
            f"learn about the technique."
        )


# -- Template-based fallback (no LLM needed) --

def _template_hint(technique: TechniqueResult, hint_level: str) -> str:
    """Generate a hint using templates when no LLM is available."""
    name = technique.technique_name
    desc = TECHNIQUE_DESCRIPTIONS.get(technique.technique_id, "")

    import re
    context = technique.explanation_context

    # Extract location from explanation context or affected cells
    location = ""
    # Try to pull a unit reference like "Row 3", "Column 5", "Box 7"
    match = re.search(r'(Row|Column|Box)\s+\d+', context)
    if match:
        location = match.group(0)
    elif technique.affected_cells:
        # Fall back to describing the area from cell coordinates
        r, c = technique.affected_cells[0]
        box = (r // 3) * 3 + c // 3 + 1
        location = f"Row {r + 1}, Column {c + 1} (Box {box})"

    if hint_level == "nudge":
        msg = f"Take a look at **{name}** in {location}." if location else f"There's a **{name}** opportunity on the board."
        msg += " See if you can spot it!"
        return msg

    elif hint_level == "introduce":
        msg = f"There's a technique called **{name}** that applies here.\n\n"
        msg += f"**What it is:** {desc}\n\n"
        if location:
            msg += f"**Where to look:** Try examining {location}.\n\n"
        msg += "Would you like to learn more about this technique? (Use the chat to ask follow-up questions if you have an LLM key configured.)"
        return msg

    else:  # skip
        return (
            f"This puzzle requires a **{name}** technique ({technique.tier} level), "
            f"which is beyond your current skill profile. You might want to try a "
            f"different puzzle, or update your skill profile if you'd like to learn about it."
        )


def _template_chat_response(message: str) -> str:
    """Fallback response when no LLM is available for chat."""
    return (
        "Chat follow-ups require an LLM API key. Set one of these environment variables:\n\n"
        "- **ANTHROPIC_API_KEY** (Claude)\n"
        "- **OPENAI_API_KEY** (ChatGPT)\n"
        "- **GEMINI_API_KEY** (Gemini — free tier available)\n\n"
        "Hints from the solver still work without a key!"
    )


# -- Public API --

async def get_hint(
    grid: list[list[int]],
    technique: TechniqueResult,
    skill_profile: dict[str, bool],
) -> str:
    hint_level = get_hint_level(technique, skill_profile)

    provider = get_provider_info()
    if not provider["available"]:
        return _template_hint(technique, hint_level)

    system = build_system_prompt(skill_profile)
    user_msg = build_hint_message(technique, hint_level, grid)

    try:
        return await complete(
            system=system,
            messages=[{"role": "user", "content": user_msg}],
        )
    except Exception as e:
        print(f"[tutor] LLM hint failed, falling back to template: {e}")
        return _template_hint(technique, hint_level)


async def chat(
    message: str,
    grid: list[list[int]],
    skill_profile: dict[str, bool],
    history: list[dict],
    last_technique: TechniqueResult | None = None,
) -> str:
    provider = get_provider_info()
    if not provider["available"]:
        return _template_chat_response(message)

    system = build_system_prompt(skill_profile)
    grid_text = format_grid_for_llm(grid)

    messages = []
    context = f"Current puzzle state:\n{grid_text}"
    if last_technique:
        elim_details = ""
        for e in last_technique.eliminations:
            r, c = e["cell"]
            elim_details += f"\n  - R{r+1}C{c+1} = {e['digit']}"
        context += (
            f"\n\nSOLVER RESULT (use this to verify the user's answers):"
            f"\n  Technique: {last_technique.technique_name} ({last_technique.tier})"
            f"\n  Context: {last_technique.explanation_context}"
            f"\n  Answer:{elim_details}"
            f"\n\nIMPORTANT: If the user asks to confirm their answer, compare it against the solver result above. "
            f"If they got the right cell and digit, confirm enthusiastically. If they got it wrong, gently redirect."
        )

    for msg in history:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({"role": role, "content": msg["content"]})

    if not messages or messages[0]["role"] != "user":
        messages.insert(0, {"role": "user", "content": context + "\n\n" + message})
    else:
        messages.append({"role": "user", "content": context + "\n\n" + message})

    # Ensure alternating roles
    cleaned = []
    for msg in messages:
        if cleaned and cleaned[-1]["role"] == msg["role"]:
            cleaned[-1]["content"] += "\n\n" + msg["content"]
        else:
            cleaned.append(msg)

    if cleaned and cleaned[0]["role"] != "user":
        cleaned.insert(0, {"role": "user", "content": context})

    try:
        return await complete(system=system, messages=cleaned)
    except Exception as e:
        print(f"[tutor] LLM chat failed: {e}")
        return f"LLM error: {e}\n\nFalling back to template mode — hints still work!"

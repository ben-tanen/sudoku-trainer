from pydantic import BaseModel


class PuzzleState(BaseModel):
    grid: list[list[int]]       # 9x9, 0 = empty
    given: list[list[int]]      # 9x9, 1 = given, 0 = user-entered
    candidates: dict[str, list[int]]  # "r1c2": [3,5,7] - manual pencil marks


class SkillProfile(BaseModel):
    naked_single: bool = True
    hidden_single: bool = True
    naked_pair: bool = False
    naked_triple: bool = False
    hidden_pair: bool = False
    hidden_triple: bool = False
    pointing_pair: bool = False
    box_line_reduction: bool = False
    x_wing: bool = False
    swordfish: bool = False
    xy_wing: bool = False
    simple_coloring: bool = False
    jellyfish: bool = False
    unique_rectangle: bool = False
    xyz_wing: bool = False
    forcing_chain: bool = False


class TechniqueResult(BaseModel):
    technique_name: str
    technique_id: str
    tier: str                            # beginner, intermediate, advanced, expert
    affected_cells: list[list[int]]      # [[row, col], ...]
    eliminations: list[dict]             # [{"cell": [r,c], "digit": d}, ...]
    explanation_context: str             # human-readable context for the LLM


class HintRequest(BaseModel):
    puzzle: PuzzleState
    skill_profile: dict[str, bool]


class ChatRequest(BaseModel):
    message: str
    puzzle: PuzzleState
    skill_profile: dict[str, bool]
    history: list[dict]  # [{"role": "user"|"tutor", "content": "..."}]
    last_technique: TechniqueResult | None = None


class HintResponse(BaseModel):
    message: str
    highlight_cells: list[list[int]] | None = None
    technique: TechniqueResult | None = None

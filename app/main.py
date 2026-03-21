from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.models import HintRequest, HintResponse, ChatRequest, OCRResponse
from app.llm import get_provider_info, extract_grid_from_image
from app.solver import analyze, get_candidates
from app.tutor import get_hint, chat as tutor_chat

app = FastAPI(title="Sudoku Trainer")


@app.get("/")
async def index():
    return FileResponse("static/index.html")


@app.post("/api/hint", response_model=HintResponse)
async def api_hint(req: HintRequest):
    technique = analyze(req.puzzle.grid, req.skill_profile)

    if technique is None:
        # Check if puzzle is complete
        empty_count = sum(1 for r in req.puzzle.grid for v in r if v == 0)
        if empty_count == 0:
            return HintResponse(message="The puzzle appears to be complete! Nice work.")
        return HintResponse(
            message="I couldn't find a technique to suggest. The puzzle state may have an error, "
                    "or it may require a technique I don't know yet. Double-check your entries."
        )

    from app.tutor import get_hint_level
    message = await get_hint(req.puzzle.grid, technique, req.skill_profile)
    hint_level = get_hint_level(technique, req.skill_profile)

    # Only highlight cells for non-nudge hints — nudges shouldn't give away the position
    highlight = technique.affected_cells if hint_level != "nudge" else None

    return HintResponse(
        message=message,
        highlight_cells=highlight,
        technique=technique,
    )


@app.post("/api/chat")
async def api_chat(req: ChatRequest):
    message = await tutor_chat(
        message=req.message,
        grid=req.puzzle.grid,
        skill_profile=req.skill_profile,
        history=req.history,
        last_technique=req.last_technique,
    )
    return {"message": message, "highlight_cells": None}


@app.post("/api/candidates")
async def api_candidates(req: HintRequest):
    candidates = get_candidates(req.puzzle.grid)
    result = {}
    for r in range(9):
        for c in range(9):
            if req.puzzle.grid[r][c] == 0 and candidates[r][c]:
                result[f"r{r+1}c{c+1}"] = sorted(candidates[r][c])
    return result


@app.post("/api/ocr", response_model=OCRResponse)
async def api_ocr(file: UploadFile = File(...)):
    allowed = {"image/png", "image/jpeg", "image/webp", "image/heic", "image/heif"}
    if file.content_type not in allowed:
        return OCRResponse(grid=[], error=f"Unsupported image type: {file.content_type}")

    image_bytes = await file.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        return OCRResponse(grid=[], error="Image too large (max 10MB)")

    try:
        grid = await extract_grid_from_image(image_bytes, file.content_type)
        return OCRResponse(grid=grid)
    except Exception as e:
        return OCRResponse(grid=[], error=f"Could not extract puzzle: {e}")


@app.get("/api/provider")
async def api_provider():
    return get_provider_info()


# Mount static files AFTER API routes so they don't shadow them
app.mount("/static", StaticFiles(directory="static"), name="static")

from fastapi import APIRouter

from cloud.app.services.eval_service import EvalService

router = APIRouter(prefix="/eval", tags=["evaluation"])

_service = EvalService()


@router.post("/run", tags=["evaluation"])
async def run_eval(body: dict):
    agent_key = body.get("agent_key", "")
    test_cases = body.get("test_cases")
    if test_cases:
        return _service.evaluate(agent_key, test_cases)
    return _service.run_regression(agent_key)


@router.get("/regression/{agent_key}", tags=["evaluation"])
async def regression(agent_key: str):
    return _service.run_regression(agent_key)


@router.get("/presets", tags=["evaluation"])
async def presets():
    return _service.PRESET_CASES

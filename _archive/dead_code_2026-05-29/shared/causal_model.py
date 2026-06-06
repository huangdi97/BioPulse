import logging
import os
import signal
import threading

logger = logging.getLogger(__name__)

_model = None
_available = False
_lock = threading.Lock()

MODEL_NAME = "microsoft/Phi-4-mini-instruct"


class _TimeoutError(Exception):
    pass


def _raise_timeout(signum, frame):
    raise _TimeoutError("model load/download timeout")


def _ensure_model():
    global _model, _available
    with _lock:
        if _model is not None:
            return
        if os.environ.get("CAUSAL_MODEL_DISABLE") == "1":
            logger.warning("CAUSAL_MODEL_DISABLE=1, skipping model load")
            _available = False
            return
        try:
            signal.signal(signal.SIGALRM, _raise_timeout)
            signal.alarm(30)
            from transformers import pipeline

            _model = pipeline(
                "text-generation",
                model=MODEL_NAME,
                device="cpu",
            )
            signal.alarm(0)
            _available = True
            logger.info("causal model loaded successfully: %s", MODEL_NAME)
        except Exception as e:
            signal.alarm(0)
            _available = False
            logger.warning("causal model load failed: %s", e)


def _rule_engine_analysis(text: str) -> dict:
    return {
        "causal_analysis": "规则引擎分析：" + text,
        "confidence": "low",
        "model_used": False,
    }


def _extract_confidence(generated_text: str) -> str:
    lower = generated_text.lower()
    if "高置信" in lower or "high confidence" in lower or "强因果" in lower:
        return "high"
    if "中等置信" in lower or "medium confidence" in lower or "可能" in lower:
        return "medium"
    return "low"


def causal_query(text: str, context: str = "") -> dict:
    _ensure_model()

    if not _available or _model is None:
        return _rule_engine_analysis(text)

    try:
        prompt = (context + " " + text + " 请分析因果关系。").strip()
        result = _model(prompt, max_new_tokens=200)
        generated = result[0]["generated_text"] if isinstance(result, list) else result["generated_text"]

        if isinstance(generated, list):
            generated = generated[0].get("generated_text", str(generated))
        if isinstance(generated, dict):
            generated = generated.get("generated_text", str(generated))
        generated = str(generated)

        confidence = _extract_confidence(generated)
        return {
            "causal_analysis": generated,
            "confidence": confidence,
            "model_used": True,
        }
    except Exception as e:
        logger.warning("causal model inference failed: %s", e)
        return _rule_engine_analysis(text)

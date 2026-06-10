"""Download DistilBERT model for Layer1 instruction filter.

Usage:
    python scripts/download_layer1_model.py

Downloads to: cloud/app/agent_runtime/models/distilbert/
"""

import logging
import os

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

MODEL_NAME = "distilbert-base-uncased"
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(
    REPO_ROOT,
    "cloud",
    "app",
    "agent_runtime",
    "models",
    "distilbert",
)


def main():
    logger.info("Downloading %s to %s ...", MODEL_NAME, MODEL_DIR)
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

    os.makedirs(MODEL_DIR, exist_ok=True)
    tokenizer.save_pretrained(MODEL_DIR)
    model.save_pretrained(MODEL_DIR)
    logger.info("Done — saved to %s", MODEL_DIR)


if __name__ == "__main__":
    main()

"""Data processing pipeline — dedup, field normalisation, HTML-to-Markdown."""

from __future__ import annotations

import hashlib
import re
from typing import Any


class DataPipeline:
    """Pipeline for cleaning and structuring raw crawl data."""

    def process(self, raw_content: str, source_type: str = "") -> dict[str, Any]:
        """Run the full pipeline: dedup, normalise, convert."""
        content = self._html_to_text(raw_content)
        content = self._normalize_whitespace(content)
        fingerprint = self._fingerprint(content)
        return {
            "content": content,
            "fingerprint": fingerprint,
            "source_type": source_type,
            "word_count": len(content.split()),
        }

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text — strip tags, decode entities."""
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"&[a-zA-Z]+;", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _normalize_whitespace(self, text: str) -> str:
        """Collapse multiple whitespace characters into single space."""
        return re.sub(r"\s+", " ", text).strip()

    def _fingerprint(self, content: str) -> str:
        """Generate a content fingerprint for deduplication."""
        normalized = re.sub(r"\s+", "", content.lower())
        return hashlib.md5(normalized.encode()).hexdigest()

    def deduplicate(self, records: list[dict[str, Any]], existing_fingerprints: set[str]) -> list[dict[str, Any]]:
        """Remove records whose fingerprints are already in the existing set."""
        result = []
        for record in records:
            fp = record.get("fingerprint", "")
            if fp and fp not in existing_fingerprints:
                existing_fingerprints.add(fp)
                result.append(record)
        return result

    def extract_structured(self, text: str, source_type: str) -> dict[str, Any]:
        """Extract structured fields from plain text."""
        title = ""
        publish_date = ""
        author = ""

        lines = text.split("\n")
        for line in lines[:20]:
            line = line.strip()
            if not title and len(line) > 10 and len(line) < 200:
                title = line
            date_match = re.search(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})", line)
            if date_match and not publish_date:
                publish_date = date_match.group(1)
            if not author and re.match(r"^(来源|作者|编辑|记者)[：:]?\s*", line):
                author = re.sub(r"^(来源|作者|编辑|记者)[：:]?\s*", "", line)

        return {
            "title": title,
            "publish_date": publish_date,
            "author": author,
        }

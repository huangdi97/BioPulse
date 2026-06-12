"""Sales coach shared utilities."""

import re
from typing import Optional


def parse_numeric_id(user_id: str) -> Optional[int]:
    """Extract trailing numeric ID from a user_id string."""
    match = re.search(r"(\d+)$", str(user_id))
    if not match:
        return None
    return int(match.group(1))

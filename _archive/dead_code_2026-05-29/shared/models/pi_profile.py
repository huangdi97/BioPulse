from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PIProfile:
    pi_id: int = 0
    name: str = ""
    hcp_id: Optional[int] = None
    institution: str = ""
    department: str = ""
    title: str = ""
    research_areas: list[str] = field(default_factory=list)
    total_papers: int = 0
    total_grants: int = 0
    h_index: int = 0
    last_updated: str = ""

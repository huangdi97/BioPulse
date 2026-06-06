"""场景数据获取模块，汇聚固定场景和知识图谱场景数据源。"""

from .scenario_builder import FIXED_SCENARIOS  # noqa: F401
from .scenario_db import _read_kg_entities  # noqa: F401

"""培训模块、会话、归因、纠正、脚本、ROI分析等数据访问层。"""

from cloud.shared.repository import BaseRepository
from shared.columns import (
    TABLE_TRAINING_ATTRIBUTIONS_COLS,
    TABLE_TRAINING_CORRECTIONS_COLS,
    TABLE_TRAINING_MODULES_COLS,
    TABLE_TRAINING_ROI_ANALYSIS_COLS,
    TABLE_TRAINING_SCRIPTS_COLS,
    TABLE_TRAINING_SESSIONS_COLS,
)


class TrainingModulesRepository(BaseRepository):
    """培训模块表。"""

    def __init__(self, db):
        super().__init__(db, "training_modules", TABLE_TRAINING_MODULES_COLS)


class TrainingSessionsRepository(BaseRepository):
    """培训会话表。"""

    def __init__(self, db):
        super().__init__(db, "training_sessions", TABLE_TRAINING_SESSIONS_COLS)


class TrainingAttributionsRepository(BaseRepository):
    """培训归因表。"""

    def __init__(self, db):
        super().__init__(db, "training_attributions", TABLE_TRAINING_ATTRIBUTIONS_COLS)


class TrainingCorrectionsRepository(BaseRepository):
    """培训纠正表。"""

    def __init__(self, db):
        super().__init__(db, "training_corrections", TABLE_TRAINING_CORRECTIONS_COLS)


class TrainingScriptsRepository(BaseRepository):
    """培训脚本表。"""

    def __init__(self, db):
        super().__init__(db, "training_scripts", TABLE_TRAINING_SCRIPTS_COLS)


class TrainingRoiAnalysisRepository(BaseRepository):
    """培训ROI分析表。"""

    def __init__(self, db):
        super().__init__(db, "training_roi_analysis", TABLE_TRAINING_ROI_ANALYSIS_COLS)

from cloud.shared.columns import (
    TABLE_TRAINING_ATTRIBUTIONS_COLS,
    TABLE_TRAINING_CORRECTIONS_COLS,
    TABLE_TRAINING_MODULES_COLS,
    TABLE_TRAINING_ROI_ANALYSIS_COLS,
    TABLE_TRAINING_SCRIPTS_COLS,
    TABLE_TRAINING_SESSIONS_COLS,
)
from cloud.shared.repository import BaseRepository


class TrainingModulesRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "training_modules", TABLE_TRAINING_MODULES_COLS)


class TrainingSessionsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "training_sessions", TABLE_TRAINING_SESSIONS_COLS)


class TrainingAttributionsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "training_attributions", TABLE_TRAINING_ATTRIBUTIONS_COLS)


class TrainingCorrectionsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "training_corrections", TABLE_TRAINING_CORRECTIONS_COLS)


class TrainingScriptsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "training_scripts", TABLE_TRAINING_SCRIPTS_COLS)


class TrainingRoiAnalysisRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "training_roi_analysis", TABLE_TRAINING_ROI_ANALYSIS_COLS)

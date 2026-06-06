"""科研轨迹特征模块，从领域模块重导出特征提取、归一化、因果归因等工具函数。"""

# Research trajectory features: re-exports from domain modules
from cloud.app.services.feature_analyzer import causal_attribution, run_prediction_fallback
from cloud.app.services.feature_extractor import extract_time_series, normalize_areas

__all__ = ["extract_time_series", "normalize_areas", "causal_attribution", "run_prediction_fallback"]

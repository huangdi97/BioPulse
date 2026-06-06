"""种子数据模块。按领域拆分为 seeds/ 子包，此处做兼容重导出。"""

from pharma_intel.app.seeds import papers, pi_profiles, targets

__all__ = ["papers", "pi_profiles", "targets"]

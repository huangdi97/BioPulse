"""SAGE 评分/排序辅助函数。"""

from datetime import datetime

from cloud.app.repositories.memory_repository import NodeMemoryLinksRepository
from cloud.app.repositories.world_tree_repository import WorldTreeNodesRepository


def normalize(value, min_val, max_val) -> float:
    """将 value 归一化到 [0, 1] 区间。"""
    if max_val <= min_val:
        return 0.0
    return (value - min_val) / (max_val - min_val)


def ts_to_epoch(ts_str):
    """时间戳字符串转 epoch 秒数。"""
    try:
        return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S").timestamp()
    except (ValueError, TypeError):
        return 0.0


def determine_tier(score):
    """按分数阈值划分 hot / warm / cold 热度层级。"""
    if score >= 70:
        return "hot"
    if score >= 30:
        return "warm"
    return "cold"


def score_episodic(repo, bms, tier_dist, comp):
    """对情景记忆条目计算 recency + utility 综合评分并写入 repo。"""
    count = 0
    ep_res = bms.episodic_list(page=1, page_size=1000)
    items = ep_res.get("items", [])
    if not items:
        return count

    ts_list = [it.get("created_at", "") for it in items]
    min_e = ts_to_epoch(min(ts_list))
    max_e = ts_to_epoch(max(ts_list))
    rng = max_e - min_e

    for it in items:
        mid = it["id"]
        ts = it.get("created_at", "")
        recency = ((ts_to_epoch(ts) - min_e) / rng) if rng > 0 else 0.5
        utility = abs(it.get("valence", 0) or 0)
        score = (recency * 0.2 + utility * 0.3 + 0.5 * 0.2) * 100
        tier = determine_tier(score)
        repo.upsert_score(
            "episodic",
            mid,
            "brain_memory",
            round(score, 2),
            tier,
            access_count=0,
            last_access=ts,
            utility_score=round(utility, 4),
            confidence=0.5,
        )
        count += 1
        tier_dist[tier] += 1
        comp["brain_memory"] += 1
    return count


def score_semantic(repo, bms, tier_dist, comp):
    """对语义记忆条目计算访问频次 + recency + 重要性综合评分。"""
    count = 0
    sem_res = bms.semantic_search("", limit=1000)
    items = sem_res.get("items", [])
    if not items:
        return count

    ts_list = [it.get("last_accessed") or it.get("created_at", "") for it in items]
    min_e = ts_to_epoch(min(ts_list))
    max_e = ts_to_epoch(max(ts_list))
    rng = max_e - min_e
    ac_vals = [it.get("access_count", 0) or 0 for it in items]
    ac_min, ac_max = min(ac_vals), max(ac_vals)

    for it in items:
        mid = it["id"]
        ts = it.get("last_accessed") or it.get("created_at", "")
        recency = ((ts_to_epoch(ts) - min_e) / rng) if rng > 0 else 0.5
        af = normalize(it.get("access_count", 0) or 0, ac_min, ac_max)
        utility = it.get("importance", 0.5) or 0.5
        score = (af * 0.3 + recency * 0.2 + utility * 0.3 + 0.5 * 0.2) * 100
        tier = determine_tier(score)
        repo.upsert_score(
            "semantic",
            mid,
            "brain_memory",
            round(score, 2),
            tier,
            access_count=it.get("access_count", 0) or 0,
            last_access=ts,
            utility_score=round(utility, 4),
            confidence=0.5,
        )
        count += 1
        tier_dist[tier] += 1
        comp["brain_memory"] += 1
    return count


def score_procedural(repo, bms, tier_dist, comp):
    """对过程记忆条目按成功率评分。"""
    count = 0
    proc_res = bms.procedural_recall("")
    items = proc_res.get("items", [])
    for it in items:
        mid = it["id"]
        utility = it.get("success_rate", 0.5) or 0.5
        score = (utility * 0.3 + 0.5 * 0.2) * 100
        tier = determine_tier(score)
        repo.upsert_score(
            "procedural",
            mid,
            "brain_memory",
            round(score, 2),
            tier,
            access_count=0,
            last_access="",
            utility_score=round(utility, 4),
            confidence=0.5,
        )
        count += 1
        tier_dist[tier] += 1
        comp["brain_memory"] += 1
    return count


def score_world_tree(repo, db, tier_dist, comp):
    """对世界树节点按子节点数、链接数、深度计算评分。"""
    count = 0
    wt_repo = WorldTreeNodesRepository(db)
    nml_repo = NodeMemoryLinksRepository(db)
    nodes = wt_repo.list_active_sorted()
    if not nodes:
        return count

    child_counts = {}
    for n in nodes:
        pid = n.get("parent_id")
        if pid is not None:
            child_counts[pid] = child_counts.get(pid, 0) + 1

    for n in nodes:
        mid = n["id"]
        cc = child_counts.get(mid, 0)
        depth = n.get("level", 0) or 0
        linked = nml_repo.count_by_node(mid)
        score = min(100, cc * 10 + linked * 5 + depth)
        tier = determine_tier(score)
        repo.upsert_score(
            "world_tree_node",
            mid,
            "world_tree",
            round(score, 2),
            tier,
            access_count=0,
            last_access=n.get("updated_at", ""),
            utility_score=0.5,
            confidence=0.5,
        )
        count += 1
        tier_dist[tier] += 1
        comp["world_tree"] += 1
    return count


class SageScoringMixin:
    """Sage 记忆评分委托方法。"""

    def _normalize(self, value, min_val, max_val) -> float:
        """将值归一化到 [0, 1] 区间。

        Args:
            value: 原始值
            min_val: 最小值
            max_val: 最大值

        Returns:
            归一化后的浮点数
        """
        return normalize(value, min_val, max_val)

    @staticmethod
    def _ts_to_epoch(ts_str):
        """将时间戳字符串转换为 Unix epoch 秒数。

        Args:
            ts_str: 时间戳字符串

        Returns:
            Unix epoch 秒数
        """
        return ts_to_epoch(ts_str)

    @staticmethod
    def _determine_tier(score):
        """根据分数判定记忆分层（hot / warm / cold）。

        Args:
            score: 记忆评分

        Returns:
            分层标签字符串
        """
        return determine_tier(score)

    def _score_episodic(self, bms, tier_dist, comp):
        """对情景记忆进行评分。

        Args:
            bms: BrainMemoryService 实例
            tier_dist: 分层分布字典（hot / warm / cold 计数）
            comp: 组件计数字典

        Returns:
            评分的记忆数量
        """
        return score_episodic(self.repo, bms, tier_dist, comp)

    def _score_semantic(self, bms, tier_dist, comp):
        """对语义记忆进行评分。

        Args:
            bms: BrainMemoryService 实例
            tier_dist: 分层分布字典
            comp: 组件计数字典

        Returns:
            评分的记忆数量
        """
        return score_semantic(self.repo, bms, tier_dist, comp)

    def _score_procedural(self, bms, tier_dist, comp):
        """对程序性记忆进行评分。

        Args:
            bms: BrainMemoryService 实例
            tier_dist: 分层分布字典
            comp: 组件计数字典

        Returns:
            评分的记忆数量
        """
        return score_procedural(self.repo, bms, tier_dist, comp)

    def _score_world_tree(self, tier_dist, comp):
        """对世界树知识图谱进行评分。

        Args:
            tier_dist: 分层分布字典
            comp: 组件计数字典

        Returns:
            评分的实体数量
        """
        return score_world_tree(self.repo, self.db, tier_dist, comp)

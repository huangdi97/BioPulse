"""轨迹录制器 — 将 agent 调用轨迹记录为 JSONL 格式。"""

import json
import os
import time
from typing import Any


class TrajectoryRecorder:
    """将 trajectory 的 input / step / final 记录到 JSONL 文件。"""

    def __init__(self, base_dir: str = "./trajectories"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _path(self, trajectory_id: str) -> str:
        return os.path.join(self.base_dir, f"{trajectory_id}.jsonl")

    def _append(self, trajectory_id: str, record: dict[str, Any]) -> None:
        path = self._path(trajectory_id)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def record_input(self, trajectory_id: str, input_data: Any) -> None:
        """记录输入。"""
        self._append(
            trajectory_id,
            {
                "trajectory_id": trajectory_id,
                "type": "input",
                "timestamp": time.time(),
                "data": input_data,
            },
        )

    def record_step(self, trajectory_id: str, step_data: Any) -> None:
        """记录中间步骤。"""
        self._append(
            trajectory_id,
            {
                "trajectory_id": trajectory_id,
                "type": "step",
                "timestamp": time.time(),
                "data": step_data,
            },
        )

    def record_final(self, trajectory_id: str, final_data: Any) -> None:
        """记录最终输出。"""
        self._append(
            trajectory_id,
            {
                "trajectory_id": trajectory_id,
                "type": "final",
                "timestamp": time.time(),
                "data": final_data,
            },
        )

    def load_trajectory(self, trajectory_id: str) -> list[dict[str, Any]]:
        """加载指定 trajectory 的所有记录。"""
        path = self._path(trajectory_id)
        records = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records

import json
import uuid
from typing import Any, Optional

from shared.base_service import BaseService


class AsrService(BaseService):
    def process_audio(self, file_path: str) -> dict[str, Any]:
        task_id = f"asr-{uuid.uuid4().hex[:12]}"
        transcript = self._mock_asr(file_path)
        summary = self.generate_summary(transcript)
        self.db.execute(
            "INSERT INTO asr_tasks (task_id, file_path, transcript, summary, status) VALUES (?, ?, ?, ?, ?)",
            (task_id, file_path, transcript, json.dumps(summary, ensure_ascii=False), "completed"),
        )
        self.db.commit()
        return {"task_id": task_id, "status": "completed"}

    def _mock_asr(self, file_path: str) -> str:
        return (
            "张主任您好，上次给您介绍的瑞达新药资料您看了吗？"
            "这个产品对糖尿病患者的血糖控制效果非常显著，"
            "临床数据显示可以有效降低糖化血红蛋白。"
            "我们希望能够在下个季度的药事会上讨论进院事宜，"
            "您看是否方便安排？另外关于价格方面，"
            "我们也可以根据医院的采购量给予一定优惠。"
        )

    def generate_summary(self, transcript: str) -> dict[str, Any]:
        return {
            "concerns": ["价格优惠幅度", "药事会排期时间"],
            "objections": ["需要更多临床数据支持"],
            "commitments": ["安排药事会讨论", "提供更多临床资料"],
            "next_steps": ["准备药事会材料", "确认价格优惠方案"],
        }

    def get_transcript(self, task_id: str) -> Optional[dict[str, Any]]:
        row = self.db.execute("SELECT task_id, transcript, status FROM asr_tasks WHERE task_id = ?", (task_id,)).fetchone()
        if not row:
            return None
        return {"task_id": row["task_id"], "transcript": row["transcript"], "status": row["status"]}

    def get_summary(self, task_id: str) -> Optional[dict[str, Any]]:
        row = self.db.execute("SELECT task_id, summary, status FROM asr_tasks WHERE task_id = ?", (task_id,)).fetchone()
        if not row:
            return None
        return {
            "task_id": row["task_id"],
            "summary": json.loads(row["summary"]) if row["summary"] else {},
            "status": row["status"],
        }

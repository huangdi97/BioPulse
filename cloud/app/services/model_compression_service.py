"""模型压缩服务，提供多种压缩策略的模拟与评估。"""

import json
import uuid
from datetime import datetime

from cloud.app.services.base import BaseService

COMPRESSION_TYPES = {
    "tensor_decomposition": {
        "name": "张量分解",
        "compression_ratio": 0.75,
        "accuracy_impact": 0.02,
        "description": "基于SVD/CP的张量分解，降低模型参数量",
    },
    "quantization": {
        "name": "量化",
        "compression_ratio": 0.6,
        "accuracy_impact": 0.012,
        "description": "INT8/FP16量化，减少模型存储和计算开销",
    },
    "pruning": {
        "name": "剪枝",
        "compression_ratio": 0.5,
        "accuracy_impact": 0.03,
        "description": "结构化/非结构化剪枝，移除冗余连接",
    },
    "knowledge_distillation": {
        "name": "知识蒸馏",
        "compression_ratio": 0.85,
        "accuracy_impact": 0.008,
        "description": "教师-学生架构，压缩为轻量模型",
    },
    "mixed": {
        "name": "混合压缩",
        "compression_ratio": 0.7,
        "accuracy_impact": 0.015,
        "description": "组合量化+剪枝+蒸馏等多种策略",
    },
    "quantum_inspired": {
        "name": "量子启发压缩",
        "compression_ratio": 0.90,
        "accuracy_impact": 0.005,
        "description": "基于CompactifAI的量子启发张量网络压缩，理论压缩比90%，精度损失<0.5%",
    },
}

BASE_PARAM_COUNTS = {
    "bert-base-chinese": 110000000,
    "bert-large-chinese": 340000000,
    "gpt2-small": 124000000,
    "gpt2-medium": 355000000,
    "gpt2-large": 774000000,
    "llama-7b": 7000000000,
    "llama-13b": 13000000000,
    "vit-base": 86000000,
    "resnet-50": 25600000,
    "t5-small": 60000000,
}


class ModelCompressionService(BaseService):
    """ModelCompression 服务类。"""

    def _estimate_size(self, param_count: int) -> int:
        return param_count * 4

    def compress(self, model_name: str, compression_type: str) -> dict:
        """compress 操作。

        Args:
            model_name: 描述
            compression_type: 描述

        Returns:
            描述
        """
        if compression_type not in COMPRESSION_TYPES:
            raise ValueError(f"不支持的压缩类型: {compression_type}")

        existing = self.db.execute(
            "SELECT * FROM model_compression_jobs WHERE model_name=? AND compression_type=? AND status='completed'",
            (model_name, compression_type),
        ).fetchone()
        if existing:
            return dict(existing)

        ct = COMPRESSION_TYPES[compression_type]
        params_before = BASE_PARAM_COUNTS.get(model_name, 50000000)
        original_size = self._estimate_size(params_before)
        compressed_size = int(original_size * (1 - ct["compression_ratio"]))
        params_after = int(params_before * (1 - ct["compression_ratio"] * 0.7))

        job_id = f"mc:{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        result_detail = json.dumps(
            {"method": ct["name"], "estimated_speedup": round(1.0 / (1 - ct["compression_ratio"] + 0.1), 2)},
            ensure_ascii=False,
        )

        self.db.execute(
            "INSERT INTO model_compression_jobs "
            "(job_id, model_name, compression_type, original_size_bytes, compressed_size_bytes, "
            "compression_ratio, accuracy_impact, parameters_before, parameters_after, "
            "status, result_detail, started_at, completed_at, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                job_id,
                model_name,
                compression_type,
                original_size,
                compressed_size,
                ct["compression_ratio"],
                ct["accuracy_impact"],
                params_before,
                params_after,
                "completed",
                result_detail,
                now,
                now,
                now,
            ),
        )
        self.db.commit()

        row = self.db.execute("SELECT * FROM model_compression_jobs WHERE job_id=?", (job_id,)).fetchone()
        return dict(row)

    def list_jobs(self, status: str | None = None) -> list[dict]:
        """list_jobs 操作。

        Args:
            status: 描述

        Returns:
            描述
        """
        if status:
            rows = self.db.execute(
                "SELECT * FROM model_compression_jobs WHERE status=? ORDER BY created_at DESC",
                (status,),
            ).fetchall()
        else:
            rows = self.db.execute("SELECT * FROM model_compression_jobs ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

    def get_job(self, job_id: str) -> dict | None:
        """get_job 操作。

        Args:
            job_id: 描述

        Returns:
            描述
        """
        row = self.db.execute("SELECT * FROM model_compression_jobs WHERE job_id=?", (job_id,)).fetchone()
        return dict(row) if row else None

    def delete_job(self, job_id: str) -> bool:
        """delete_job 操作。

        Args:
            job_id: 描述

        Returns:
            描述
        """
        cur = self.db.execute("DELETE FROM model_compression_jobs WHERE job_id=?", (job_id,))
        self.db.commit()
        return cur.rowcount > 0

    def get_available_types(self) -> list[dict]:
        """get_available_types 操作。

        Returns:
            描述
        """
        return [{"key": k, **v} for k, v in COMPRESSION_TYPES.items()]

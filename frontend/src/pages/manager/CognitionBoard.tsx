import React, { useEffect, useState } from "react";

const API_BASE = "/api/v1/world-model";

interface Cognition {
  cognition_id: string;
  pattern: string;
  description: string;
  confidence: number;
  evidence: string[];
  agent_keys: string[];
  detected_at: string;
}

export default function CognitionBoard() {
  const [cognitions, setCognitions] = useState<Cognition[]>([]);
  const [loading, setLoading] = useState(true);
  const [confidenceFilter, setConfidenceFilter] = useState(0);
  const [agentFilter, setAgentFilter] = useState("");

  useEffect(() => {
    const params = new URLSearchParams();
    if (confidenceFilter > 0) params.set("min_confidence", String(confidenceFilter));
    if (agentFilter) params.set("agent_key", agentFilter);

    fetch(`${API_BASE}/cognitions?${params}`)
      .then((r) => r.json())
      .then((data) => {
        setCognitions(data.cognitions || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [confidenceFilter, agentFilter]);

  const confidenceColor = (c: number) => {
    if (c >= 0.7) return "border-l-green-500";
    if (c >= 0.4) return "border-l-yellow-500";
    return "border-l-gray-400";
  };

  const confidenceLabel = (c: number) => {
    if (c >= 0.7) return "高";
    if (c >= 0.4) return "中";
    return "低";
  };

  const agentLabel: Record<string, string> = {
    compliance_monitor: "合规",
    competitor_crawler: "竞品",
    sales_suggestion: "建议",
    anomaly_analysis: "分析",
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-900">认知看板</h1>
        <p className="text-sm text-gray-500 mt-1">世界模型发现的跨域模式关联</p>
      </div>

      {/* 筛选 */}
      <div className="flex gap-4 mb-6">
        <select
          value={confidenceFilter}
          onChange={(e) => setConfidenceFilter(Number(e.target.value))}
          className="px-3 py-2 text-sm border border-gray-300 rounded-lg"
        >
          <option value={0}>全部置信度</option>
          <option value={0.7}>高 (≥0.7)</option>
          <option value={0.4}>中 (≥0.4)</option>
        </select>
        <select
          value={agentFilter}
          onChange={(e) => setAgentFilter(e.target.value)}
          className="px-3 py-2 text-sm border border-gray-300 rounded-lg"
        >
          <option value="">全部Agent</option>
          <option value="compliance_monitor">合规</option>
          <option value="competitor_crawler">竞品</option>
          <option value="sales_suggestion">建议</option>
          <option value="anomaly_analysis">分析</option>
        </select>
      </div>

      {/* 认知卡片 */}
      {loading ? (
        <div className="text-center text-gray-400 py-12">加载中...</div>
      ) : cognitions.length === 0 ? (
        <div className="text-center text-gray-400 py-12">暂无认知发现</div>
      ) : (
        <div className="grid gap-4">
          {cognitions.map((c) => (
            <div
              key={c.cognition_id}
              className={`bg-white rounded-lg border border-gray-200 border-l-4 shadow-sm p-5 ${confidenceColor(c.confidence)}`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-semibold text-gray-800">{c.pattern}</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">
                  {confidenceLabel(c.confidence)}置信
                </span>
              </div>
              <p className="text-sm text-gray-600 mb-3">{c.description}</p>
              <div className="flex flex-wrap gap-2 mb-2">
                {c.agent_keys.map((k) => (
                  <span key={k} className="text-xs px-2 py-0.5 rounded bg-blue-50 text-blue-600">
                    {agentLabel[k] || k}
                  </span>
                ))}
              </div>
              {c.evidence.length > 0 && (
                <details className="text-xs text-gray-400 mt-2">
                  <summary className="cursor-pointer hover:text-gray-600">证据来源 ({c.evidence.length})</summary>
                  <ul className="mt-1 space-y-0.5 pl-4 list-disc">
                    {c.evidence.map((e, i) => (
                      <li key={i}>{e}</li>
                    ))}
                  </ul>
                </details>
              )}
              <div className="text-xs text-gray-400 mt-2">
                发现时间: {c.detected_at?.slice(0, 16).replace("T", " ")}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
